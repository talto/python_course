package main

import (
	"bufio"
	"compress/gzip"
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"sync/atomic"

	"github.com/bradfitz/gomemcache/memcache"
	"google.golang.org/protobuf/proto"

	"loader/pb"
)

const normalErrRate = 0.01

type appsInstalled struct {
	devType string
	devID   string
	lat     float64
	lon     float64
	apps    []uint32
}

type mcTarget struct {
	addr   string
	client *memcache.Client
}

type job struct {
	line string
}

func parseLine(line string) (*appsInstalled, error) {
	parts := strings.Split(strings.TrimSpace(line), "\t")
	if len(parts) < 5 {
		return nil, errors.New("bad columns")
	}
	devType, devID, latS, lonS, rawApps := parts[0], parts[1], parts[2], parts[3], parts[4]
	if devType == "" || devID == "" {
		return nil, errors.New("empty dev fields")
	}

	var apps []uint32
	for _, a := range strings.Split(rawApps, ",") {
		a = strings.TrimSpace(a)
		if a == "" {
			continue
		}
		for _, ch := range a {
			if ch < '0' || ch > '9' {
				a = ""
				break
			}
		}
		if a == "" {
			continue
		}
		var v uint64
		_, err := fmt.Sscanf(a, "%d", &v)
		if err != nil {
			continue
		}
		apps = append(apps, uint32(v))
	}

	var lat, lon float64
	if _, err := fmt.Sscanf(latS, "%f", &lat); err != nil {
		return nil, fmt.Errorf("bad lat: %w", err)
	}
	if _, err := fmt.Sscanf(lonS, "%f", &lon); err != nil {
		return nil, fmt.Errorf("bad lon: %w", err)
	}

	return &appsInstalled{devType, devID, lat, lon, apps}, nil
}

func insert(mc *memcache.Client, memcAddr string, ai *appsInstalled, dry bool) error {
	msg := &pb.UserApps{
		Lat:  &ai.lat,
		Lon:  &ai.lon,
		Apps: ai.apps,
	}
	key := fmt.Sprintf("%s:%s", ai.devType, ai.devID)
	data, err := proto.Marshal(msg)
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	if dry {
		log.Printf("D %s -> %s apps=%d lat=%.6f lon=%.6f", memcAddr, key, len(ai.apps), ai.lat, ai.lon)
		return nil
	}
	if err := mc.Set(&memcache.Item{Key: key, Value: data}); err != nil {
		return fmt.Errorf("memcache set: %w", err)
	}
	return nil
}

func dotRename(path string) error {
	dir := filepath.Dir(path)
	base := filepath.Base(path)
	return os.Rename(path, filepath.Join(dir, "."+base))
}

func processGZFile(filename string, deviceMC map[string]mcTarget, workers int, dry bool) {
	log.Printf("I Processing %s", filename)

	f, err := os.Open(filename)
	if err != nil {
		log.Printf("E open: %v", err)
		_ = dotRename(filename)
		return
	}
	defer f.Close()

	gzr, err := gzip.NewReader(f)
	if err != nil {
		log.Printf("E gzip: %v", err)
		_ = dotRename(filename)
		return
	}
	defer gzr.Close()

	sc := bufio.NewScanner(gzr)
	sc.Buffer(make([]byte, 0, 64*1024), 16*1024*1024)

	jobs := make(chan job, workers*4)
	var processed, errorsCnt int64
	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			for j := range jobs {
				ai, err := parseLine(j.line)
				if err != nil || ai == nil {
					atomic.AddInt64(&errorsCnt, 1)
					continue
				}
				tgt, ok := deviceMC[ai.devType]
				if !ok || tgt.client == nil {
					log.Printf("E unknown device type: %s", ai.devType)
					atomic.AddInt64(&errorsCnt, 1)
					continue
				}
				if err := insert(tgt.client, tgt.addr, ai, dry); err != nil {
					log.Printf("E write: %v", err)
					atomic.AddInt64(&errorsCnt, 1)
					continue
				}
				atomic.AddInt64(&processed, 1)
			}
		}()
	}

	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		jobs <- job{line: line}
	}
	if err := sc.Err(); err != nil {
		log.Printf("E scan: %v", err)
	}

	close(jobs)
	wg.Wait()

	p := atomic.LoadInt64(&processed)
	e := atomic.LoadInt64(&errorsCnt)
	if p == 0 {
		_ = dotRename(filename)
		return
	}
	errRate := float64(e) / float64(p)
	if errRate < normalErrRate {
		log.Printf("I Acceptable error rate (%.4f). Successful load", errRate)
	} else {
		log.Printf("E High error rate (%.4f > %.2f). Failed load", errRate, normalErrRate)
	}
	_ = dotRename(filename)
}

func main() {
	var (
		pattern = flag.String("pattern", "./*.gz", "glob pattern for input .gz files containing .tsv data")
		logfile = flag.String("log", "", "log file (stdout if empty)")
		dry     = flag.Bool("dry", false, "dry run: do not write to memcached")
		workers = flag.Int("workers", 8, "number of worker goroutines")
		idfa    = flag.String("idfa", "127.0.0.1:33013", "memcached addr for idfa")
		gaid    = flag.String("gaid", "127.0.0.1:33014", "memcached addr for gaid")
		adid    = flag.String("adid", "127.0.0.1:33015", "memcached addr for adid")
		dvid    = flag.String("dvid", "127.0.0.1:33016", "memcached addr for dvid")
	)
	flag.Parse()

	if *logfile != "" {
		f, err := os.OpenFile(*logfile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
		if err != nil {
			log.Fatalf("open log: %v", err)
		}
		defer f.Close()
		log.SetOutput(f)
	}

	wd, _ := os.Getwd()
	log.Printf("I start: dry=%v workers=%d cwd=%q pattern=%q", *dry, *workers, wd, *pattern)

	deviceMC := map[string]mcTarget{
		"idfa": {addr: *idfa, client: memcache.New(*idfa)},
		"gaid": {addr: *gaid, client: memcache.New(*gaid)},
		"adid": {addr: *adid, client: memcache.New(*adid)},
		"dvid": {addr: *dvid, client: memcache.New(*dvid)},
	}

	files, err := filepath.Glob(*pattern)
	if err != nil {
		log.Fatalf("glob: %v", err)
	}
	sort.Strings(files)
	if len(files) == 0 {
		log.Printf("W no files matched pattern %q (cwd=%q)", *pattern, wd)
		return
	}
	log.Printf("I matched %d file(s)", len(files))

	for _, fn := range files {
		processGZFile(fn, deviceMC, *workers, *dry)
	}
}

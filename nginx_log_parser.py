import argparse
import json

from log_parser import parse_file


def main():
    parser = argparse.ArgumentParser(
        description="Парсинг логов Nginx и генерация отчёта."
    )
    parser.add_argument("-f", "--file", required=True, help="Путь к файлу логов")
    parser.add_argument("-o", "--output", help="Путь для сохранения отчёта (JSON)")

    args = parser.parse_args()

    report_data = parse_file(args.file)
    report_json = json.dumps(report_data, indent=4, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report_json)
        print(f"Отчёт сохранён в: {args.output}")
    else:
        print(report_json)


if __name__ == "__main__":
    main()

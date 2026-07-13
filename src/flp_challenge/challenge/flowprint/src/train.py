import csv
import json
import sys

CLASSES = ["Android", "iOS", "Windows", "Linux", "Chromium OS", "Mac OS"]

LABEL_COLUMN = "device_os"
MIN_VALUE_COUNT = 20
RARE_VALUE = "__rare__"


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _bucket_ttl(value):
    ttl = _to_float(value)
    if ttl <= 0:
        return "unknown"
    if ttl <= 64:
        return "64"
    if ttl <= 128:
        return "128"
    return "255"


def _normalize(value):
    if value is None:
        return "missing"
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return "missing"
    try:
        number = float(text)
    except ValueError:
        return text
    if number == int(number):
        return str(int(number))
    return text


def extract_value(row, feature):
    if feature == "ip_ttl_bucket":
        return _bucket_ttl(row.get("ip_ttl"))
    return _normalize(row.get(feature))


def get_feature_names(fieldnames):
    if not fieldnames:
        return []
    return [field for field in fieldnames if field != LABEL_COLUMN]


def _prune_table(table):
    pruned = {}
    rare = dict.fromkeys(CLASSES, 0)
    for value, class_counts in table.items():
        if sum(class_counts.values()) >= MIN_VALUE_COUNT:
            pruned[value] = class_counts
        else:
            for c in CLASSES:
                rare[c] += class_counts.get(c, 0)
    if sum(rare.values()) > 0:
        pruned[RARE_VALUE] = rare
    return pruned


def main():
    train_csv = sys.argv[1]
    model_json = sys.argv[2]

    with open(train_csv, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        feature_names = get_feature_names(reader.fieldnames)
        count = {feature: {} for feature in feature_names}
        class_totals = dict.fromkeys(CLASSES, 0)

        for row in reader:
            label = str(row.get(LABEL_COLUMN, "")).strip()
            if label not in class_totals:
                continue
            class_totals[label] += 1
            for feature in feature_names:
                value = extract_value(row, feature)
                table = count[feature]
                if value not in table:
                    table[value] = dict.fromkeys(CLASSES, 0)
                table[value][label] += 1

    count = {feature: _prune_table(table) for feature, table in count.items()}
    default_class = max(class_totals, key=class_totals.get)
    model = {
        "version": 2,
        "features": feature_names,
        "classes": CLASSES,
        "class_total": class_totals,
        "default_class": default_class,
        "counts": count,
    }
    with open(model_json, "w", encoding="utf-8") as model_file:
        json.dump(model, model_file, separators=(",", ":"))


if __name__ == "__main__":
    main()

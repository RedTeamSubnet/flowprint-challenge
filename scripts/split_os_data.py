from pathlib import Path

import pandas as pd


def main() -> None:
    data_dir = Path("volumes/storage/flowradar-challenge/data")
    source_path = data_dir / "flow_data_sampled_350k.csv"
    train_path = data_dir / "os_train_data.csv"
    test_path = data_dir / "os_test_data.csv"

    df = pd.read_parquet(source_path)
    if "device_os" not in df.columns:
        raise SystemExit("Missing required label column: device_os")

    train_parts = []
    test_parts = []
    for _, group in df.groupby("device_os", dropna=False):
        group = group.sample(frac=1, random_state=42).reset_index(drop=True)
        split_index = int(len(group) * 0.8)
        train_parts.append(group.iloc[:split_index])
        test_parts.append(group.iloc[split_index:])

    train = (
        pd.concat(train_parts)
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )
    test = (
        pd.concat(test_parts)
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )

    train.to_csv(train_path, index=False)
    test.to_csv(test_path, index=False)

    print(f"source rows: {len(df)}")
    print(f"train rows:  {len(train)} -> {train_path}")
    print(f"test rows:   {len(test)} -> {test_path}")
    print()
    print("train labels:")
    print(train["device_os"].value_counts())
    print()
    print("test labels:")
    print(test["device_os"].value_counts())


if __name__ == "__main__":
    main()

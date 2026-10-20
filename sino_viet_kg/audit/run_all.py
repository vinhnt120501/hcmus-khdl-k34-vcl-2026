"""Chạy tuần tự audit gold-free (Mục 3.5, 4.3 — Bảng 3).

  python3 -m sino_viet_kg.audit.run_all                 # mọi bước, bỏ qua bước đã xong
  python3 -m sino_viet_kg.audit.run_all --force         # chạy lại tất cả
  python3 -m sino_viet_kg.audit.run_all --only 02_dictionary
  python3 -m sino_viet_kg.audit.run_all --from 02_dictionary
"""
import argparse
import importlib

from sino_viet_kg.audit import state as S

ORDER = [s for s, _ in S.STEPS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="chạy lại cả bước đã xong")
    ap.add_argument("--only", choices=ORDER, help="chỉ chạy 1 bước")
    ap.add_argument("--from", dest="start", choices=ORDER, help="chạy từ bước này trở đi")
    args = ap.parse_args()

    steps = ORDER
    if args.only:
        steps = [args.only]
    elif args.start:
        steps = ORDER[ORDER.index(args.start):]

    for s in steps:
        if not args.force and not args.only and S.read_state(s).get("status") == "done":
            print(f"[bỏ qua] {s} (đã xong)")
            continue
        print(f"\n== {s} ==")
        importlib.import_module(f"sino_viet_kg.audit.step{s}").run()


if __name__ == "__main__":
    main()

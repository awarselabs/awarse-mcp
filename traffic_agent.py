from daily_growth_digest import build_report, dispatch_report

if __name__ == "__main__":
    digest = build_report()
    dispatch_report(digest)

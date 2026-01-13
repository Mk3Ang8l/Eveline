import threading
from datetime import datetime


class DataCollector:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self._lock = threading.Lock()

    def add_result(self, result):
        """Adds a result and enriches it with a discovery timestamp."""
        with self._lock:
            result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.results.append(result)

    def get_results(self):
        with self._lock:
            # Sort alphabetically by platform before returning
            return sorted(self.results, key=lambda x: x['platform'])

    def aggregate_by_category(self):
        """Groups results by platform category (Social, Gaming, etc.)."""
        categories = {}
        for res in self.results:
            cat = res.get('category', 'Miscellaneous')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(res)
        return categories

    def get_stats(self):
        """Generates metrics for the final summary."""
        total = len(self.results)
        found = [r for r in self.results if r['status'] == "FOUND"]

        duration = datetime.now() - self.start_time
        return {
            "total_checked": total,
            "total_found": len(found),
            "success_rate": f"{(len(found) / total) * 100:.2f}%" if total > 0 else "0%",
            "scan_duration": str(duration).split(".")[0]
        }

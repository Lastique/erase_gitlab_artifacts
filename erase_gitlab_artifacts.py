#!/usr/bin/env python3
#
# Andrey Semashev, 2025
#
# The script erases artifacts of a GitLab project.

import json
import argparse
import logging
import http.client

# Number of jobs to list per page
JOBS_PER_PAGE = 100
# Number of consecutive empty pages to stop after
EMPTY_PAGES_TO_STOP = 1

# Loads a page worth of jobs from the server and returns their ids. Filters out incomplete or already erased jobs.
def load_jobs_page(conn, base_path, page, headers):
	path = base_path + f"/jobs/?page={page}&per_page={JOBS_PER_PAGE}"
	logging.info(f"Loading jobs page {page}: {path}")
	conn.request("GET", path, headers = headers)

	resp = conn.getresponse()
	if int(resp.status // 100) != 2:
		raise RuntimeError(f"Fetching jobs page {page} failed, server returned error {resp.status} {resp.reason}")

	data = json.load(resp)
	logging.debug(json.dumps(data))
	job_ids = []
	for job in data:
		if job.get("id") is not None and job.get("finished_at") is not None and job.get("erased_at") is None:
			job_ids.append(job.get("id"))

	return job_ids

# Erases a job with the given id
def erase_job(conn, base_path, job_id, headers, ignore_errors):
	path = base_path + f"/jobs/{job_id}/erase"
	logging.info(f"Erasing job {job_id}: {path}")
	conn.request("POST", path, headers = headers)

	resp = conn.getresponse()
	if int(resp.status // 100) != 2:
		descr = f"Erasing job {job_id} failed, server returned error {resp.status} {resp.reason}"
		if ignore_errors:
			logging.warning(descr)
		else:
			raise RuntimeError(descr)

	resp.read()

def main():
	try:
		arg_parser = argparse.ArgumentParser(description = "The script permanently erases artifacts of a GitLab project.")
		arg_parser.add_argument("-H", "--host", default = "gitlab.com", help = "GitLab instance hostname (default: gitlab.com)")
		arg_parser.add_argument("-p", "--project", required = True, help = "GitLab project id")
		arg_parser.add_argument("-T", "--token", required = True, help = "Access token for the project (must have \"api\" permission)")
		arg_parser.add_argument("-k", "--keep", default = 0, type = int, help = "Number of the most recent artifacts to keep (default: 0)")
		arg_parser.add_argument("-I", "--ignore-errors", action = "store_true", help = "Ignore errors returned by server for artifact erasing requests")
		arg_parser.add_argument("-v", "--verbose", default = logging.INFO, type = int, help = f"Logging level verbosity (default: {logging.INFO})")
		args = arg_parser.parse_args()

		logging.getLogger().setLevel(args.verbose)

		conn = http.client.HTTPSConnection(host = args.host)
		conn.connect()

		base_path = f"/api/v4/projects/{args.project}"
		headers = { "PRIVATE-TOKEN": args.token }
		page = 0
		job_index = 0
		empty_pages = 0
		while empty_pages < EMPTY_PAGES_TO_STOP:
			job_ids = load_jobs_page(conn, base_path, page, headers)
			if len(job_ids) > 0:
				empty_pages = 0

				for job_id in job_ids:
					if job_index >= args.keep:
						erase_job(conn, base_path, job_id, headers, args.ignore_errors)

					job_index += 1
			else:
				empty_pages += 1

			page += 1

		logging.info("Done.")
	except Exception:
		logging.exception("Failure")

if __name__ == "__main__":
	main()

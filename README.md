# Utility to erase artifacts of a GitLab project

This utlity can be useful to mitigate continuous growth of storage consumption
for a GitLab project that regularly runs CI jobs (autobuilds, autotests,
deployment, etc.). Users are able to set up a CI job that will run periodically
and erase outdated artifacts to free storage space.

NOTE: Artifact removal is irreversible. Since the script is intended to be run
automatically, it will not ask questions and will go ahead and remove whatever
was specified on the command line. *BE CAREFUL AND USE AT YOUR OWN RISK!*
The author is not responsible for any data loss that may be caused by this
utility.

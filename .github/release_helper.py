from contextlib import contextmanager
import os
import git
import datetime


NEW_THRESHOLD = 100
DAY_THRESHOLD = 1


REPOSITORY = "../"


# Get the third most recent tag, which is the last release
# Don't use positive number (e.g., 0, 1, 2, etc) as it will be sorted in reverse
# [-1]: Nightly
# [-2]: v2.12.0 - last release
# [-3]: v2.11.0 - second last release
last_release = sorted(git.Repo(REPOSITORY).tags, key=lambda t: t.commit.committed_datetime)[-2].name


def is_workflow_dispatch() -> bool:
  """
  Check if the event is manually dispatched, support GitHub/GitLab/Forgejo

  GITHUB_EVENT_NAME: GitHub Actions, Forgejo (GitHub compatibility)

  CI_PIPELINE_SOURCE: GitLab CI

  Returns:
    bool: True if the event is manually dispatched, False otherwise
  """

  if os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch" or os.getenv("CI_PIPELINE_SOURCE") == "web":
    return True
  return False


@contextmanager
def git_checkout(repo: git.Repo, ref: str):
  """
  Temporarily check out a specific git reference

  Allow to check out a specific git reference temporarily and return to the 
  original reference after the context manager exits.
  
  Args:
    repo (git.Repo): The git repository
    ref (str): The reference to check out
  """
  
  original_ref = repo.active_branch.name if repo.head.is_detached else repo.head.ref.name
  repo.git.checkout(ref)
  try:
    yield
  finally:
    repo.git.checkout(original_ref)


def get_new_icon_since(last_version: str) -> list:
  """
  Get the new icons since the last release
  
  Args:
    last_version (str): The last release version

  Returns:
    list: List of new icons
  """
  
  icons_dir = '../svgs'
  
  current_icons = set(os.listdir(icons_dir))
  
  print(f"Checking out version {last_version}")
  with git_checkout(git.Repo(REPOSITORY), last_version):
    previous_icons = set(os.listdir(icons_dir))
      
  return list(current_icons - previous_icons)


def is_greenlight(result: list, manually_triggered: bool, day_threshold = 1, new_threshold = 100) -> bool:
  """Check if the new icons meet the threshold for release
  
  Args:
    result (list): List of new icons
    manually_triggered (bool): Check if the workflow is manually dispatched
    day_threshold (int, optional): Number of days to check. Defaults to 1.
    new_threshold (int, optional): Number of new icons to check. Defaults to 100.
  Returns:
    bool: True if the new icons is eligible for release, False otherwise, will skip all checks if manually triggered"""
  
  if manually_triggered:
    print("🟢 Manually triggered workflow, skipped all check, greenlighting!")
    return True
    
  today_day = datetime.datetime.now().day
  if today_day != day_threshold:
    print(f"🔴 Today is {today_day}, which isn't the target release day {day_threshold}.")
    return False
  
  if len(result) < new_threshold:
    print(f"🔴 Only {len(result)} new icons found since the last release, below the threshold of {new_threshold}.")
    return False

  print("🟢 Greenlight!")
  return True


result = get_new_icon_since(last_release)
print(f"🎉 There have been {len(result)} new icons since release!")

greenlight = is_greenlight(result, is_workflow_dispatch(), DAY_THRESHOLD, NEW_THRESHOLD)
print(f"🚦 {'Not eligible for release!' if not greenlight else 'Eligible for release! Greenlight away!'}")

exit(1 if not greenlight else 0)

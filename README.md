Github Watcher
==============

Github Watcher is a daemon that monitors the files/ line ranges and directories you configure it to. When there is a pull request sent making a change to that directory or those line ranges in those files; you'll get an OSX notification. There's also a really annoying voice that tells you what was found.

Installation
------------

I don't really feel like packaging this, so just pull the source and run the file directly. You'll need to create a github access token with `repo` and `user` permissions. Add that token to a file at `~/.github`. We'll need it to authenticate with your repos.

Configuration
-------------

Github Watcher expects a `.yml` formatted config file at `~/.watch-github.yml`. The file should be of the format:

```yaml
---

username:
  repository_name:
    filepath1:
      - [starting_line1, stopping_line1]
      - [starting_line2, stopping_line2]
    filepath2:
      - [starting_line1, stopping_line1]
    directory_path: null
```

So, for example, if I wanted to watch [this](https://github.com/akellehe/fb_calendar/blob/8cc6e867aa67732fab869872eec7586fd1a9c0c2/deploy/roles/fb_calendar_api/tasks/main.yml#L30-L40) line range I would use the configuration:

```yaml
akellehe:
  fb_calendar:
    deploy/roles/fb_calendar_api/tasks/main.yml
      - [30, 40]
```

Or if I wanted to watch the whole `deploy/` directory I would use:

```yaml
akellehe:
  fb_calendar:
    deploy/: null
```

Execution
---------

To run this after it's configured you can just do:

```bash
python watcher.py
```

If you want to run it in the background you can do:

```bash
python watcher.py &
```

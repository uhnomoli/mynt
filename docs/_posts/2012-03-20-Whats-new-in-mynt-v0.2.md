---
layout: post.html
title: 'What''s new in mynt v0.2'
tags: ['Releases']
---

With v0.2 comes a handful of changes to make working with mynt sites easier. Now available are `init`, `watch`, and `serve` commands. Also, along with these new commands comes a default theme. Lastly, to accompany these changes is a reworked [quickstart][quickstart] guide. The goal of these changes being to make mynt more accessible.


# Commands

The biggest of these changes is the addition of three new commands. The first of which being `init`. The `init` command allows you to quickly setup a new site either using the new default theme or a bare directory structure.

Next is the `watch` command. Now instead of having to manually regenerate your site every time you've made a change you can now use the `watch` command which will automatically regenerate your site whenever a change in the source is detected.

Lastly, there is the `serve` command. If you don't have a local server setup, you can now use the `serve` command to quickly host your site locally for developing and testing.

To read more on the new commands and how to use them, check out the [directory structure][directory-structure] and [commands][commands] sections of the quickstart guide.


# Default theme

Now included with mynt is a default theme. The default theme comes with an annotated config file and a handful of useful built-in features, such as an Atom feed and the easy addition of profile links to various social sites.

To get started with the new default theme, use the new `init` command.

```text
$ mynt init ~/projects/my-site/
```

You can see it in action right here as the new mynt site is using the new default theme.


# Getting started

If you're new to mynt or are curious about the changes in v0.2 give the reworked [quickstart][quickstart] guide a read. Hopefully the reworked quickstart guide will give a better overview on how to get started with mynt and the features it has available.

Getting started with v0.2 is only a quick `pip` away!

```text
$ pip install mynt
```


[commands]: {{ get_url('docs/quickstart/#commands') }}
[directory-structure]: {{ get_url('docs/quickstart/#directory-structure') }}
[quickstart]: {{ get_url('docs/quickstart/') }}

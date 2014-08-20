---
layout: post.html
title: 'What''s new in mynt v0.3'
tags: ['Releases']
---

It's been almost two and a half years since the last major release and a lot has changed. I'm happy to finally announce the release of mynt v0.3 and with it comes a handful of new features and a lot of bug fixes.


# Content containers

The headlining feature of v0.3 is the new content containers. With this new feature you can define containers that are handled exactly like posts, but are separate. They also support the same tagging and archives features as posts all the while allowing you to use a supported markup language to write your content. To learn more check out the relevant sections of the [quickstart][quickstart] guide and [config][config] documentation.


# Markup pages

Also new in v0.3 is the ability to write pages in the supported markup languages. All that's required to do so is a YAML frontmatter with the `layout` attribute set. Be sure to check out the new [pages][pages] section of the quickstart guide for more information.


# And more

Be sure to check out the [changelog][changelog] for a comprehensive list of changes as well as the [upgrading][upgrading] page if you are looking to migrate an existing site as several backwards incompatible changes were made.


[changelog]: {{ get_url('miscellany/changelog/#v0.3') }}
[config]: {{ get_url('docs/config/#containers') }}
[pages]: {{ get_url('docs/quickstart/#pages') }}
[quickstart]: {{ get_url('docs/quickstart/#content-containers') }}
[upgrading]: {{ get_url('miscellany/upgrading/#v0.2.x-to-v0.3.x') }}

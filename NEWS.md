# News

### v0.3.1 (August 20th, 2014)

+ __Changed__
    + Removed the `<hr>` from and added classes to the outputted markup for Markdown footnotes.
    + Tag data is now stored in an object instead of a dictionary.


### v0.3 (July 27th, 2014)

+ __New__
    + A mechanism for defining content containers.
    + Two new filters for the Jinja renderer, `items` and `values`, that act as syntactic sugar for `iteritems()` and `itervalues()`.
    + A reStructuredText parser.
    + Two new `item` properties, `prev` and `next`, that store the previous and next items in the container.
    + Files outside of ignored directories will now be parsed if a parser is available.
    + Two config settings for controlling how posts are sorted: `posts_order` and `posts_sort`.
+ __Changed__
    + Global and local dictionaries no longer behave different from ordinary Python dictionaries when iterating over them.
    + The `archives` and `tags` globals are now properties of the `posts` global to maintain consistency between content containers.
    + The `post` local has been renamed `item` to maintain consistency between content containers.
    + The `<title>` variable in URL formats has been renamed to `<slug>`.
    + Frontmatter attributes that contain string values can now be used in URL formats.
    + The `markup` and `parser` config settings have been removed.
    + Which parser used is now determined by _(in order of precedence)_ the `parser` frontmatter attribute, the `parser` container config setting, and lastly the file extension.
    + In Markdown, the bracket fenced code block syntax is no longer supported.
    + The `layout` frontmatter attribute can now be set to `None` to skip rendering.


### v0.2.3 (June 13th, 2013)

+ __New__
    + A new default theme with dark (default) and light versions.
    + A config setting for specifying directories and files to be copied over that would otherwise be ignored.
    + Localization and internationalization support.
+ __Changed__
    + The programming language of a code block is now stored in the `data-lang` attribute of the `<code>` tag instead of the `lang` attribute of the `<pre>` tag.
    + Tildes are no longer allowed in post slugs.
    + The `watch` subcommand now honors the configured log level.
+ __Upgraded__
    + Jinja 2.7
+ __Fixed__
    + A bug in the handling of log messages in the `serve` subcommand.
    + A bug in the misaka parser with SmartyPants.
    + A bug in the `serve` subcommand when handling paths containing Unicode characters.
    + A bug in the `watch` subcommand when a file is moved into the directory that is being watched.
    + A bug when handling an empty config file.


### v0.2.2 (April 11th, 2012)

+ __Upgraded__
    + misaka 1.0.2
+ __Fixed__
    + A bug in the `absolutize` filter of the Jinja renderer.
    + A bug in the `get_url` template helper where it was appending a forward slash when it shouldn't.


### v0.2.1 (March 20th, 2012)

+ __Fixed__
    + The default theme not getting installed.


### v0.2 (March 20th, 2012)

+ __New__
    + An archive property is now available for tags in the tags global.
    + A default theme.
    + Four new subcommands: `init`, `gen`, `watch`, and `serve`.
+ __Changed__
    + Archive years and tag names are always available in their respective globals.
    + When the destination already exists on generation, it is now emptied by default instead of deleted.
    + Generation is now done via the `gen` subcommand.
+ __Fixed__
    + A bug when retrieving the URL for an archive page.
    + A regression in the misaka renderer when generating semantic identifiers.


### v0.1.9 (March 12th, 2012)

+ __New__
    + An absolute URL can now be retrieved via the `get_url` template helper if the `domain` config setting has been set.
    + A filter for the Jinja render that attempts to convert all relative URLs to absolute URLs.
+ __Changed__
    + The misaka parser now automatically escapes code blocks.
+ __Fixed__
    + A Unicode issue in the misaka parser.
    + An escaping issue with code highlighting.
    + A bug in the Jinja renderer when handling Windows paths.


### v0.1.8 (February 8th, 2012)

+ __Upgraded__
    + miaska 1.0


### v0.1.7 (January 30th, 2012)

+ __Changed__
    + The `excerpt` post property is no longer wrapped in a `<p>` tag.
+ __Fixed__
    + A bug in the misaka parser when the Markdown source parses out to nothing.


### v0.1.6 (January 25th, 2012)

+ __Fixed__
    + An import issue preventing installation.


### v0.1.5 (January 25th, 2012)

+ __Fixed__
    + An import issue preventing installation.


### v0.1.4 (January 2nd, 2012)

+ __Fixed__
    + A type issue in `setup.py`.


### v0.1.3 (January 2nd, 2012)

+ __New__
    + A version flag.
+ __Changed__
    + Removed the `year` and `name` properties from archives and tags respectively.


### v0.1.2 (December 27th, 2011)

+ __New__
    + Posts are now partially rendered before being parsed enabling renderer functionality within posts.
    + The hour and minute of a post can now be set with it defaulting to the file's `mtime`.
    + Archive pages can now be automatically generated.
+ __Changed__
    + Identifiers will now be semantic when using misaka's TOC render flag.
    + Removed the `slug` property from posts.
+ __Fixed__
    + A bug when parsing posts with no content.
    + Post and tag URLs not being properly slugified.
    + A Unicode issue with dates.


### v0.1.1 (December 4th, 2011)

+ __Changed__
    + Added a `name` attribute to tags.
+ __Fixed__
    + A bug with extensionless files.
    + A bug when using the `-qv` flags.


### v0.1 (December 4th, 2011)

_Initial release._

# News

### 0.2.3 (unreleased)

+ __New__
    + Localization and internationalization support.
    + A config setting for specifying directories and files to be copied over that would otherwise be ignored.
    + A new default theme with dark (default) and light versions.
+ __Changed__
    + The `watch` subcommand now honors the configured log level.
    + Tildes are no longer allowed in post slugs.
    + The programming language of a code block is now stored in the `data-lang` attribute of the `<code>` tag instead of the `lang` attribute of the `<pre>` tag.
    + HTML escaping is now handled by Houdini.
+ __Upgraded__
    + Jinja 2.7
+ __Fixed__
    + A bug in the `watch` subcommand when a file is moved into the directory that is being watched.
    + A bug in the `serve` subcommand when handling paths containing Unicode characters.
    + A bug in the misaka parser with SmartyPants.
    + A bug in the handling of log messages in the `serve` subcommand.


### 0.2.2 (April 11th, 2012)

+ __Upgraded__
    + misaka 1.0.2
+ __Fixed__
    + A bug in the `get_url` template helper where it was appending a forward slash when it shouldn't.
    + A bug in the `absolutize` filter of the Jinja renderer.


### 0.2.1 (March 20th, 2012)

+ __Fixed__
    + The default theme not getting installed.


### 0.2 (March 20th, 2012)

+ __New__
    + Four new subcommands: `init`, `gen`, `watch`, and `serve`.
    + A default theme.
    + An archive property is now available for tags in the tags global.
+ __Changed__
    + Generation is now done via the `gen` subcommand.
    + When the destination already exists on generation, it is now emptied by default instead of deleted.
    + Archive years and tag names are always available in their respective globals.
+ __Fixed__
    + A regression in the misaka renderer when generating semantic identifiers.
    + A bug when retrieving the URL for an archive page.


### 0.1.9 (March 12th, 2012)

+ __New__
    + A filter for the Jinja render that attempts to convert all relative URLs to absolute URLs.
    + An absolute URL can now be retrieved via the `get_url` template helper if the `domain` config setting has been set.
+ __Changed__
    + The misaka parser now automatically escapes code blocks.
+ __Fixed__
    + A bug in the Jinja renderer when handling Windows paths.
    + An escaping issue with code highlighting.
    + A Unicode issue in the misaka parser.


### 0.1.8 (February 8th, 2012)

+ __Upgraded__
    + miaska 1.0


### 0.1.7 (January 30th, 2012)

+ __Changed__
    + The `excerpt` post property is no longer wrapped in a `<p>` tag.
+ __Fixed__
    + A bug in the misaka parser when the Markdown source parses out to nothing.


### 0.1.6 (January 25th, 2012)

+ __Fixed__
    + An import issue. _(really this time)_


### 0.1.5 (January 25th, 2012)

+ __Fixed__
    + An import issue.


### 0.1.4 (January 2nd, 2012)

+ __Fixed__
    + A type issue in `setup.py`.


### 0.1.3 (January 2nd, 2012)

+ __New__
    + A version flag.
+ __Changed__
    + Removed the `year` and `name` properties from archives and tags respectively.


### 0.1.2 (December 27th, 2011)

+ __New__
    + Archive pages can now be automatically generated.
    + The hour and minute of a post can now be set with it defaulting to the file's `mtime`.
    + Posts are now partially rendered before being parsed enabling renderer functionality within posts.
+ __Changed__
    + Removed the `slug` property from posts.
    + Identifiers will now be semantic when using misaka's TOC render flag.
+ __Fixed__
    + A Unicode issue with dates.
    + Post and tag URLs not being properly slugified.
    + A bug when parsing posts with no content.


### 0.1.1 (December 4th, 2011)

+ __Changed__
    + Added a `name` attribute to tags.
+ __Fixed__
    + A bug when using the `-qv` flags.
    + A bug with extensionless files.


### 0.1 (December 4th, 2011)

_Initial release._

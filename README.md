## What this is for
This small script was made to get word lists for the German language for
[monkeytype]. It gets data from https://pcai056.informatik.uni-leipzig.de and
parses the information to generate the appropriate files.


## Quirks

_Since_ the original data analysed the frequency of words in written German,
lots of the German word appear capitalized since the often go at the start
of a sentence. Like with the word "since" you would not expect it to be
capitalized in a string of random words like you type on monkeytype. This is why
this script converts _a lot_ of words to lowercase.

In case the words were taken from news at source there are also lots of
political parties, names and abbreviations in the source data. I tried to strip
all abbreviations and as much other Non-German as I could. But the list is
certainly not exhaustive.

I tired to remove all single occurrence words but I was left with less than 250k
words which is one of the existing categories in monkeytype. It will take the
single occurrence words in alphabetical order starting with capital letter
words.


## Issues

There is currently no filter for inappropriate words. I believe the current
words list for German is not filtered for that as well, since it does contain
"Arschloch" for example.

It is a lot of work to go through all words and find Names or special cases in
the raw word list. I think it would be better to implements an API to check if
the words are German – e.g. query against the [Duden API].


## Potential Features

If wanted, I could add the option for other quantities of words, like 2k, or add
an option for configuring quantity as a parameter.


## Problems

I currently don't know how I could integrate this into the [monkeytype] project
besides opening a PR once in a while with an updated list.
- I do not just the source to be stable enough for automation
- I do not know if Wikipedia or News are preferred as base
- I am too unhappy with the manual filter to submit a result to monkeytype (see
  [Issues](#issues)


[monkeytype]: https://github.com/monkeytypegame/monkeytype
[Duden API]: https://www.duden.de/api

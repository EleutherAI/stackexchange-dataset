# stackexchange_dataset

[![Build unstable](https://github.com/lfoppiano/stackexchange-dataset/actions/workflows/ci-build.yml/badge.svg)](https://github.com/lfoppiano/stackexchange-dataset/actions/workflows/ci-build.yml)

A python tool for downloading & processing the [stackexchange data dumps](https://archive.org/details/stackexchange) into a text dataset for Language Models.

**NOTE**: The original repository seems not maintained anymore. This includes additional fixes. See [Todo](#todo)

[//]: # (Download the whole processed dataset [here]&#40;https://eaidata.bmk.sh/data/stackexchange_dataset.tar&#41;)

## Setup
```
git clone https://github.com/EleutherAI/stackexchange_dataset/
cd stackexchange_dataset
pip install -r requirements.txt
```
## Usage


### List all available StackExchagne dumps

```
python3 main.py --list 
```

### Download every StackExchange dumps 

To download *every* stackexchange dumps & parse to text, simply run

```
python3 main.py --names all
```

### Download a single StackExchange dump 

To download only a single stackexchange, you can add the name as an optional argument. E.G: 

```
python3 main.py --names security.stackexchange
```

### Download a list of StackExchange dumps

To download a list of multiple stackexchanges, you can add the names separated by commas. E.G:

```
python3 main.py --names ru.stackoverflow,money.stackexchange
```

The name should be the url of the stackoverflow site, minus `http(s)://` and `.com`. You can view all available stackoverflow dumps [here](https://archive.org/download/stackexchange).

## List available sources in Stack Exchange

this will list all the available sources: 

```
python3 main.py --list
```

They will be listed as list, which could be parsed with `grep` and other batch utilities.


## All Usage Options:

```
usage: main.py [-h] [--names NAMES]

CLI for stackexchange_dataset - A tool for downloading & processing
stackexchange dumps in xml form to a raw question-answer pair text dataset for
Language Models

options:
  -h, --help            show this help message and exit
  --list                list of all the sources from stackechange
  --names NAMES         names of stackexchanges to download, extract & parse, separated by commas. If "all", will download, extract & parse *every* stackoverflow site
  --out_format {txt,lm_dataformat,json}
                        format of out file - if you are processing everything this will need to be lm_dataformat, as you will run into number of files per directory limits.
  --min_score MIN_SCORE
                        minimum score of a response in order to be included in the dataset. Default 3.
  --max_responses MAX_RESPONSES
                        maximum number of responses (sorted by score) to include for each question. Default 3.
  --keep-sources        Do not clean-up the downloaded source 7z files.

```

### Proxy support 

If you need to pass through a proxy, you can configure an `.env` file and add as follow: 

```
HTTP_PROXY=http://proxy:port
http_proxy=http://proxy:port
HTTPS_PROXY=http://proxy:port
https_proxy=http://proxy:port
NO_PROXY=address to ignore,localhost
no_proxy=address to ignore,localhost
```

## Formats 

This fork supports the following formats: txt,lm_dataformat,json

### Text (txt)

The output is stored in a ZIP file. 

```
Q:

Pantsing a story?

I heard a writer talking about pantsing a story. What does that mean?

A:

"Pantsing" refers to simply writing a story without much, if any, preparation or pre-writing -- just writing down whatever comes to you, and letting the story go (and wander) wherever it feels like at the moment you're writing it down.
As for etymology, I'm not sure where it comes from. In general, "pantsing" refers to a prank in which you pull someone's pants down, but I'm not sure how that plays into the idea of writing (aside from the fact that both can be surprising).
```

### JSONL

The output is stored in a ZST zipped file with the following JSON in it: 

```jsonl
  {
    "question": {
      "title": "How should we behave for the \"reference\" questions?",
      "body": "Suppose user X comes in and ask \"How is the group with professor Y at university Z ?\". How should we treat this kind of questions ? One thing may be to answer with pure citation metrics, that is: they publish a lot, or they don't seem to. More personal experiences and opinions about Professor Y may trigger complaint from the professor him\/herself.\n"
    },
    "answers": [
      {
        "id": "3",
        "body": "I think questions about specific people or specific departments are not good questions for this site.  It would be much better for the asker to directly contact students of the department\/person in question.\n",
        "score": 12
      }
    ]
  }
  [...]
```


# TODO: 

- [ ] read Post.xml directly in 7z files by streaming 
- [ ] should we add metadata to the text (i.e name of stackexchange & tags)?
- [x] add flags to change min_score / max_responses args.
- [x] ~~add flags to turn off downloading / extraction~~ add flag to keep sources after download 
- [x] add flags to select number of workers for multiprocessing
- [x] output as [lm dataformat](https://github.com/leogao2/lm_dataformat)
- [x] output as structured JSON output

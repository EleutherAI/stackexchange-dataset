# stackexchange_dataset
A python tool for downloading & processing the [stackexchange data dumps](https://archive.org/details/stackexchange) into a text dataset for Language Models.

Download the whole processed dataset [here](https://eaidata.bmk.sh/data/stackexchange_dataset.tar)

# Setup
```
git clone https://github.com/EleutherAI/stackexchange_dataset/
cd stackexchange_dataset
pip install -r requirements.txt
```
# Usage

To download *every* stackexchange dump & parse to text, simply run

```
python3 main.py --names all
```

To download only a single stackexchange, you can add the name as an optional argument. E.G: 

```
python3 main.py --names security.stackexchange
```

To download a list of multiple stackexchanges, you can add the names separated by commas. E.G:

```
python3 main.py --names ru.stackoverflow,money.stackexchange
```

The name should be the url of the stackoverflow site, minus `http(s)://` and `.com`. You can view all available stackoverflow dumps [here](https://archive.org/download/stackexchange).

## All Usage Options:

```
usage: main.py [-h] [--names NAMES]

CLI for stackexchange_dataset - A tool for downloading & processing
stackexchange dumps in xml form to a raw question-answer pair text dataset for
Language Models

optional arguments:
  -h, --help     show this help message and exit
  --names NAMES  names of stackexchanges to download, extract & parse,
                 separated by commas. If "all", will download, extract & parse
                 *every* stackoverflow site
```

# TODO:

- [ ] should we add metadata to the text (i.e name of stackexchange & tags)?
- [ ] add flags to change min_score / max_responses args.
- [ ] add flags to turn off downloading / extraction
- [ ] add flags to select number of workers for multiprocessing
- [ ] output as [lm dataformat](https://github.com/leogao2/lm_dataformat)


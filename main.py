import argparse, traceback
from multiprocessing import Pool, cpu_count
from utils import *
from downloader import Stack_Exchange_Downloader
from pairer import QA_Pairer

# TODO: should we add metadata to the text (i.e name of stackexchange & tags)?
#       add flags to change min_score / max_responses args
#       add flags to turn off downloading / extraction


def download_and_process_single(name):
    try:
        os.makedirs("dumps", exist_ok=True)
        s = Stack_Exchange_Downloader(name)
        s.download()
        s.extract()
        os.remove("dumps/{}.com.7z".format(name.replace("https://", "").replace("http://", "").replace(".com", "")))
        path_to_xml = "dumps/{}/Posts.xml".format(name)
        qa = QA_Pairer(path_to_xml, name)
        qa.main()
    except:
        traceback.print_exc()


def main(args):
    names = args.names.split(',')
    if names[0]=="all":
        s = Stack_Exchange_Downloader("all")
        names = []
        for k in s.sites:
            names.append(k)
    print('Downloading and processing stackexchange dumps for {}'.format(names))
    # init pool with as many CPUs as available
    cpu_no = cpu_count() - 1
    p = Pool(cpu_no)
    # Download & Process
    p.map(download_and_process_single, names)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='CLI for stackexchange_dataset - A tool for downloading & processing stackexchange dumps in xml form to a raw '
                    'question-answer pair text dataset for Language Models')
    parser.add_argument('--names', help='names of stackexchanges to download, extract & parse, separated by commas. '
                                        'If "all", will download, extract & parse *every* stackoverflow site',
                        default="security.stackexchange",
                        type=str)
    args = parser.parse_args()
    main(args)



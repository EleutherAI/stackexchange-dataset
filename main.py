import argparse, traceback
from multiprocessing import Pool, cpu_count
from utils import *
from downloader import Stack_Exchange_Downloader
from pairer import QA_Pairer
import os
from itertools import repeat
from lm_dataformat import Archive
import zipfile


def download_and_process_single(name, out_format, min_score, max_responses):
    try:
        name = name.strip().lower()
        os.makedirs("dumps", exist_ok=True)
        s = Stack_Exchange_Downloader(name)
        path_to_xml = "dumps/{}/Posts.xml".format(name)
        if name != "stackoverflow":
            path_to_7z = "dumps/{}.7z".format(s.sites[name]["url"])
        else:
            path_to_7z = "dumps/stackoverflow.com-Posts.7z"
        out_folder = "out".format(name)
        os.makedirs(out_folder, exist_ok=True)
        if not os.path.isfile(path_to_7z):
            # download 7z if it's not downloaded already
            s.download()
        if not os.path.isfile(path_to_xml):
            # extract 7z if it's not extracted already
            s.extract()
        if out_format == "lm_dataformat":
            archiver = Archive(out_folder)
        elif out_format == "zip":
            archiver = zipfile.ZipFile('{}/{}.zip'.format(out_folder, name), 'a')
        else:
            archiver = None
        qa = QA_Pairer(path_to_xml, name=name, out_format=out_format, archiver=archiver, min_score=min_score, max_responses=max_responses)
        qa.main()
        if out_format == "lm_dataformat":
            archiver.commit(name)
        elif out_format == "zip":
            archiver.close()
        try:
            os.remove(path_to_7z)
        except FileNotFoundError:
            print('ERROR: FileNotFoundError: File {} not found'.format(s.sites[name]["url"]))
        filelist = [f for f in os.listdir("dumps/{}".format(name)) if f.endswith(".xml")]
        for f in filelist:
            os.remove(os.path.join("dumps/{}".format(name), f))
    except:
        traceback.print_exc()


def main(args):
    names = args.names.split(',')
    if names[0].strip().lower() == "all":
        s = Stack_Exchange_Downloader("all")
        names = []
        for k in s.sites:
            names.append(k)
        # bring stackoverflow to the front so it is always processed first, since it's the largest
        if "stackoverflow" in names:
            names.insert(0, names.pop(names.index("stackoverflow")))
    print('Downloading and processing stackexchange dumps for {}'.format(names))
    # Download & Process
    # init pool with as many CPUs as available
    cpu_no = cpu_count() - 1
    p = Pool(cpu_no)
    p.starmap(download_and_process_single, zip(names, repeat(args.out_format), repeat(args.min_score), repeat(args.max_responses)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='CLI for stackexchange_dataset - A tool for downloading & processing stackexchange dumps in xml form to a raw '
                    'question-answer pair text dataset for Language Models')
    parser.add_argument('--names', help='names of stackexchanges to download, extract & parse, separated by commas. '
                                        'If "all", will download, extract & parse *every* stackoverflow site',
                        default="3dprinting.stackexchange,3dprinting.meta.stackexchange",
                        type=str)
    parser.add_argument('--out_format', help='format of out file - if you are processing everything this will need to be '
                                             'lm_dataformat, as you will run into number of files per directory limits.',
                        default="zip",
                        type=str)
    parser.add_argument('--min_score', help='minimum score of a response in order to be included in the dataset. Default 3.',
                        type=int, default=3)
    parser.add_argument('--max_responses', help='maximum number of responses (sorted by score) to include for each question. '
                                                'Default 3.', type=int, default=3)
    args = parser.parse_args()
    main(args)



import argparse
import os
import traceback
from itertools import repeat
from multiprocessing import Pool, cpu_count

import dotenv
from lm_dataformat import Archive, JSONArchive, TextArchive, LM_DATAFORMAT_FORMAT, TEXT_FORMAT, SUPPORTED_FORMATS, \
    JSON_FORMAT

from downloader import Stack_Exchange_Downloader
from pairer import QA_Pairer

dotenv.load_dotenv(override=True)


def download_and_process_single(name, out_format, min_score, max_responses, keep_sources=False):
    try:
        name = name.strip().lower()
        os.makedirs("dumps", exist_ok=True)
        s = Stack_Exchange_Downloader(name)
        if name not in s.sites:
            similar_entries = list(filter(lambda key: key.startswith(name) or key.endswith(name), s.sites.keys()))
            print("StackExchange source not found. Perhaps you meant", similar_entries)
            return

        path_to_xml = "dumps/{}/Posts.xml".format(name)
        if name != "stackoverflow":
            path_to_7z = "dumps/{}.7z".format(s.sites[name]["url"])
        else:
            path_to_7z = "dumps/stackoverflow.com-Posts.7z"

        out_folder = "out/{}".format(name)
        os.makedirs(out_folder, exist_ok=True)
        if not os.path.isfile(path_to_7z):
            # download 7z if it's not downloaded already
            s.download()

        valid = s.validate()
        if valid is False:
            s.download()
            # s.remove_dump()

        if out_format == JSONL_FORMAT:
            archiver = Archive(out_folder)
        elif out_format == TEXT_FORMAT:
            archiver = TextArchive(out_folder)
        else:
            archiver = None

        if not os.path.isfile(path_to_xml):
            # extract 7z if it's not extracted already
            s.extract()

        qa = QA_Pairer(path_to_xml, name=name, out_format=out_format, archiver=archiver, min_score=min_score,
                       max_responses=max_responses)
        qa.process()
        archiver.commit(name)

        if not keep_sources:
            try:
                os.remove(path_to_7z)
            except FileNotFoundError:
                print('ERROR: FileNotFoundError: File {} not found'.format(s.sites[name]["url"]))

        directory_uncompressed = "dumps/{}".format(name)
        filelist = [f for f in os.listdir(directory_uncompressed)
                    if f.endswith(".xml")]
        for f in filelist:
            os.remove(os.path.join(directory_uncompressed, f))
        os.removedirs(directory_uncompressed)
    except:
        traceback.print_exc()


def main(args):
    if args.list:
        s = Stack_Exchange_Downloader("all")
        print("List of all the sources of StackExchange: ")
        print("- " + "\n- ".join(sorted(s.sites.keys())))
        return

    names = args.names.split(',')
    if names[0].strip().lower() == "all":
        s = Stack_Exchange_Downloader("all")
        names = []
        for k in s.sites:
            names.append(k)
        # bring stackoverflow to the front, so it is always processed first, since it's the largest
        if "stackoverflow" in names:
            names.insert(0, names.pop(names.index("stackoverflow")))
        # if args.no_zip:
        #     print("Downloading everything required the output to be compressed. Re-run *without* the option --no-zip.")
        #     sys.exit(-1)
    print('Downloading and processing stackexchange dumps for {}'.format(names))
    # Download & Process
    # init pool with as many CPUs as available
    if args.max_num_threads < 1:
        cpu_no = cpu_count() - 1
    else:
        cpu_no = args.max_num_threads

    p = Pool(cpu_no)
    p.starmap(download_and_process_single,
              zip(names, repeat(args.out_format), repeat(args.min_score), repeat(args.max_responses),
                  repeat(args.keep_sources)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='CLI for stackexchange_dataset - A tool for downloading & processing stackexchange dumps in xml form to a raw '
                    'question-answer pair text dataset for Language Models')

    parser.add_argument('--list', help='list of all the sources from stackechange',
                        required=False, action="store_true")

    parser.add_argument('--names', help='names of stackexchanges to download, extract & parse, separated by commas. '
                                        'If "all", will download, extract & parse *every* stackoverflow site',
                        default="3dprinting.stackexchange,3dprinting.meta.stackexchange",
                        type=str)
    parser.add_argument('--out_format',
                        help='format of out file - if you are processing everything this will need to be '
                             'lm_dataformat, as you will run into number of files per directory limits.',
                        default=TEXT_FORMAT,
                        choices=SUPPORTED_FORMATS,
                        type=str)
    # parser.add_argument('--no-zip',
    #                     help="Disable the compression of the output files. Writing plain files might end up in problems with the filesystem",
    #                     action="store_true",
    #                     required=False,
    #                     default=False)
    parser.add_argument('--min_score',
                        help='minimum score of a response in order to be included in the dataset. Default 3.',
                        type=int, default=3)
    parser.add_argument('--max_responses',
                        help='maximum number of responses (sorted by score) to include for each question. '
                             'Default 3.', type=int, default=3)
    parser.add_argument('--keep-sources',
                        help='Do not clean-up the downloaded source 7z files.',
                        action="store_true",
                        default=False)
    parser.add_argument("--use-disk",
                        help="Use a disk-backed collection for sources larger than 1Gb. "
                             "NOTE that might need several Gb of temporary files "
                             "(consider set your own temp directory using --temp-directory)",
                        default=False,
                        action="store_true")
    parser.add_argument('--temp-directory',
                        help='Set a custom temporary directory root, instead of the OS designated. '
                             'This process ran on the full stackexchange collection may need several Gb of temporary files.',
                        required=False,
                        default=None)
    parser.add_argument('--max-num-threads',
                        help="Set the maximum thread number. If not specified will use the number of CPU - 1. "
                             "If --use-disk is not specified, using a large amount of thread might end up in a out of "
                             "memory and being killed by the OS.",
                        required=False,
                        default=-1,
                        type=int)
    args = parser.parse_args()

    main(args)

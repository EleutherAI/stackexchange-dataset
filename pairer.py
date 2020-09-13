import traceback
import xml.etree.ElementTree as etree
from collections import defaultdict
from bs4 import BeautifulSoup
from tqdm import tqdm
from utils import *


class QA_Pairer():

    def __init__(self, xml_path, name=None, out_folder="out", min_score=3, max_responses=3, out_format="txt", archiver=None):
        """Makes a text dataset from StackExchange dumps"""
        self.xml_path = xml_path
        if name is None:
            self.name = os.path.dirname(xml_path).replace("dumps/", "")
        else:
            self.name = name
        # dict to save questions
        self.questions = defaultdict(lambda: None, {})
        # folder to save txt files to
        self.out_folder = out_folder
        # min_score required to parse an answer
        self.min_score = min_score
        self.max_responses = max_responses
        assert out_format in ["txt", "lm_dataformat", "zip"], "Out format not recognized"
        self.out_format = out_format
        if out_format in ["lm_dataformat", "zip"]:
            assert archiver is not None
            self.ar = archiver

    def main(self):
        """iterates through SE xmls and:

        - stores PostTypeId="1" with AcceptedAnswerIds / Answers.
        - when an AcceptedAnswerId or Answer > min_score is reached, it should:
            > concat the Question & Accepted answer
            > Clean markup / HTML
            > Output to txt file
            > Delete from memory

        """
        os.makedirs(self.out_folder, exist_ok=True)
        for event, elem in tqdm(etree.iterparse(self.xml_path, events=('end',)), desc="Parsing {} XML file".format(self.name)):
            if elem.tag == "row":
                try:
                    attribs = defaultdict(lambda: None, elem.attrib)
                    if is_question(attribs):
                        if has_answers(attribs):
                            trim_attribs(attribs, "question")
                            self.questions[attribs["Id"]] = attribs
                        else:
                            # if the question has no answers, discard it
                            continue
                    elif is_answer(attribs):
                        # if is accepted answer, append answer Body to relevant questions "AcceptedAnswer" field
                        # if the answer's score > min_score
                        # append the answer to the relevant question's OtherAnswers dict
                        self.add_answer(attribs)
                        self.check_complete(attribs)
                    elem.clear()
                except:
                    traceback.print_exc()

    def is_above_threshold(self, a_attribs):
        """
        Determines whether an answer is above the min_score threshold

        :param a_attribs: Answer's attribute dict
        :return:
        """
        assert is_answer(a_attribs), "Must be an answer to be above threshold"
        if a_attribs["Score"] is not None:
            if int(a_attribs["Score"]) >= self.min_score:
                return True
        return False

    def add_answer(self, a_attribs):
        """
        Adds answer to its parent question in self.questions if it's either an accepted answer or above self.min_score.
         If answer is an accepted answer, it gets appended to the AcceptedAnswer field, otherwise it gets appended to
         OtherAnswers.

         Also increments the question's 'ParsedAnswers' field. When ParsedAnswers = AnswerCount, the question is deleted
         from memory and saved to a text file.

        :param a_attribs: Answer's attribute dict
        """
        assert is_answer(a_attribs), "Must be an answer to add to parent"
        if a_attribs is not None and self.questions[a_attribs["ParentId"]] is not None:
            if is_accepted_answer(a_attribs, self.questions[a_attribs["ParentId"]]):
                self.questions[a_attribs["ParentId"]]["Answers"][a_attribs["Id"]] = trim_attribs(a_attribs, "answer")
                self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1
            elif self.is_above_threshold(a_attribs):
                if a_attribs["Id"] is not None:
                    parent = self.questions[a_attribs["ParentId"]]
                    if parent is not None:
                        self.questions[a_attribs["ParentId"]]["Answers"][a_attribs["Id"]] = trim_attribs(a_attribs, "answer")
                        self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1
                else:
                    self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1
            else:
                self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1

    def check_complete(self, a_attribs):
        """
        checks if the parent question of the previously added answer has no future answers, and if so,
        removes from dict and prints to file.
        """
        keys_to_del = []
        parent = self.questions[a_attribs["ParentId"]]
        if a_attribs is not None and parent is not None:
            if parent["AnswerCount"] is not None and parent["ParsedAnswers"] is not None:
                if int(parent["ParsedAnswers"]) == int(parent['AnswerCount']):
                    keys_to_del.append(a_attribs["ParentId"])
                    if parent["Answers"] is not None and len(parent["Answers"]) > 0:
                        out_name = "{}_{}.txt".format(self.name, parent["Id"].zfill(10))
                        out_str = ""
                        out_str += 'Q:\n\n'
                        if parent["Title"] is not None:
                            out_str += '{}\n\n'.format(BeautifulSoup(parent["Title"], "html.parser").get_text())
                        if parent["Body"] is not None:
                            out_str += '{}\n\n'.format(BeautifulSoup(parent["Body"], "html.parser").get_text())
                        if parent["Answers"] is not None:
                            key_score_dict = {}
                            for k, a in parent["Answers"].items():
                                key_score_dict[k] = int(a["Score"])
                            key_score_dict = {k: v for k, v in sorted(key_score_dict.items(), key=lambda item: item[1], reverse=True)}
                            count = 0
                            for k in key_score_dict:
                                if count >= self.max_responses:
                                    break
                                out_str += 'A:\n\n{}\n\n'.format(BeautifulSoup(parent["Answers"][k]["Body"], "html.parser").get_text())
                                count += 1
                        if self.out_format == "txt":
                            with open("{}/{}".format(self.out_folder, out_name), 'w') as f:
                                try:
                                    f.write(filter_newlines(out_str))
                                except:
                                    f.write(filter_newlines(handle_unicode_errors(out_str)))
                        elif self.out_format == "zip":
                            try:
                                self.ar.writestr(out_name, filter_newlines(out_str))
                            except:
                                self.ar.writestr(out_name, filter_newlines(handle_unicode_errors(out_str)))
                        elif self.out_format == "lm_dataformat":
                            try:
                                self.ar.add_data(filter_newlines(out_str), meta={
                                    'name': out_name})
                            except:
                                self.ar.add_data(filter_newlines(handle_unicode_errors(out_str)), meta={
                                    'name': out_name})
        for key in keys_to_del:
            self.questions.pop(key, None)

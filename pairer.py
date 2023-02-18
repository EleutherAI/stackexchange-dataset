import traceback
import xml.etree.ElementTree as etree
from collections import defaultdict, OrderedDict
from bs4 import BeautifulSoup
from tqdm import tqdm
from utils import *


class QA_Pairer():

    def __init__(self, xml_path, name=None, out_folder="out", min_score=3, max_responses=3, out_format="txt", archiver=None):
        """Makes a text dataset from StackExchange dumps"""
        self.xml_path = xml_path
        if name is None:
            self.name = os.path.dirname(xml_path).replace("*dumps/", "")
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
        self.sample = True 
        self.num_posts = 0
        self.num_nonQA_posts = 0
        self.num_discarded_answers = 0
        self.num_discarded_questions = 0
        self.num_questions = 0
        self.num_answers = 0 

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
        for event, elem in tqdm(etree.iterparse(self.xml_path, events=('end',)), desc="Parsing {} XML file".format(self.name), disable=True):
            if elem.tag == "row":
                try:
                    attribs = defaultdict(lambda: None, elem.attrib)
                    self.num_posts += 1
                    # checks if PostTypeId=1
                    if is_question(attribs):
                        if has_answers(attribs):
                            # trim post data to  ['Id', 'Body', 'Title', 'Tags', 'AnswerCount', 'AcceptedAnswerId', 'PostTypeId']
                            # other potentially usuful keys: ['CreationDate',  'Score', 'ViewCount', 'OwnerUserId', 'LastActivityDate', 'CommentCount', 'ContentLicense']
                            trim_attribs(attribs, "question")
                            self.questions[attribs["Id"]] = attribs
                        else:
                            # if the question has no answers, discard it
                            self.num_discarded_questions += 1
                            continue
                    # checks if PostTypeId=2
                    elif is_answer(attribs):
                        # if is accepted answer, append answer Body to relevant questions "AcceptedAnswer" field
                        # if the answer's score > min_score append the answer to the relevant question's OtherAnswers dict
                        self.add_answer(attribs)
                        self.check_complete(attribs)
                    else:
                        self.num_nonQA_posts += 1
                    elem.clear()
                except:
                    traceback.print_exc()
        
        print("##### Stats #####")
        print(f"num_questions={self.num_questions}, num_discarded_questions={self.num_discarded_questions}")
        print(f"num_answers={self.num_answers}, num_discarded_answers={self.num_discarded_answers}")
        print(f"num_posts={self.num_posts}, num_nonQA_posts={self.num_nonQA_posts}")
        unprocessed_questions = len(self.questions.items())
        unprocessed_answers = sum([len(q_att['Answers'].items()) for q, q_att in self.questions.items()])
        print(f"unprocessed_questions={unprocessed_questions}, unprocessed_answers={unprocessed_answers}")
        print("###### End ######")

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
        If answer is an accepted answer, it gets appended to the AcceptedAnswer field, otherwise it gets appended to OtherAnswers.

        Also increments the question's 'ParsedAnswers' field. When ParsedAnswers = AnswerCount, the question is deleted from memory and saved to a text file.

        :param a_attribs: Answer's attribute dict
        """
        assert is_answer(a_attribs), "Must be an answer to add to parent"
        if self.questions.get(a_attribs["ParentId"], None) is not None:
            if is_accepted_answer(a_attribs, self.questions[a_attribs["ParentId"]]):
                self.questions[a_attribs["ParentId"]]["Answers"][a_attribs["Id"]] = trim_attribs(a_attribs, "answer")
                self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1
            elif self.is_above_threshold(a_attribs):
                self.questions[a_attribs["ParentId"]]["Answers"][a_attribs["Id"]] = trim_attribs(a_attribs, "answer")
                self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1
            else:                
                self.num_discarded_answers += 1 
                # print("Discarded answer with score {}".format(a_attribs["Score"]), self.num_discarded_answers)
                self.questions[a_attribs["ParentId"]]["NonAnswers"][a_attribs["Id"]] = trim_attribs(a_attribs, "answer")
                self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1
        else: 
            parentid = a_attribs["ParentId"]            
            self.num_discarded_answers += 1
            # print(f"ParentId {parentid} not found", self.num_discarded_answers)

    def check_complete(self, a_attribs):
        """
        checks if the parent question of the previously added answer has no future answers, and if so,
        removes from dict and prints to file.
        """
        keys_to_del = []
        parent = self.questions.get(a_attribs["ParentId"], None)
        if a_attribs is not None and parent is not None:
            if parent["AnswerCount"] and parent["ParsedAnswers"]:
                if int(parent["ParsedAnswers"]) == int(parent['AnswerCount']):
                    keys_to_del.append(a_attribs["ParentId"])
                    ## Filter change: still use quesions with no accepted answers
                    # if parent["Answers"] is not None and len(parent["Answers"]) > 0:
                    if 1:
                        out_tags = tags_as_list(parent["Tags"])
                        out_name = "{}_{}_{}.txt".format(self.name, parent["Id"].zfill(10),"_".join(out_tags))
                        out_dict = dict(
                            name=out_name,
                            tags=out_tags,
                            title=BeautifulSoup(parent["Title"], "html.parser").get_text(),
                            question=BeautifulSoup(parent["Body"], "html.parser").get_text(),
                            answers=[],
                            answers_scores=[],
                            non_answers=[],
                            non_answers_scores=[]
                        )
                        # fmt: "Q:\n\n{question.title}\n\n{question.body}\n\nA:\n\n{answer.body\n\n for answer.sortby(score)}"                        
                        out_str = ""
                        out_str += 'Q:\n\n'
                        if parent["Title"] is not None:
                            out_str += '{}\n\n'.format(BeautifulSoup(parent["Title"], "html.parser").get_text())
                        if parent["Body"] is not None:
                            out_str += '{}\n\n'.format(BeautifulSoup(parent["Body"], "html.parser").get_text())
                        if parent["Answers"] is not None:
                            key_score_dict = {}
                            for ans_id, ans_attrib in parent["Answers"].items():
                                key_score_dict[ans_id] = int(ans_attrib["Score"])
                            key_score_dict = OrderedDict((ans_id, score) for ans_id, score in sorted(key_score_dict.items(), key=lambda item: item[1], reverse=True))
                            count = 0
                            for ans_id, score in key_score_dict.items():
                                if count >= self.max_responses:
                                    break
                                ans_text = BeautifulSoup(parent["Answers"][ans_id]["Body"], "html.parser").get_text()
                                out_str += 'A:\n\n{}\n\n'.format(ans_text)
                                out_dict['answers'].append(ans_text)
                                out_dict['answers_scores'].append(score)
                                count += 1

                        if parent["NonAnswers"] is not None:
                            nona_key_score_dict = {}
                            for ans_id, ans_attrib in parent["NonAnswers"].items():
                                nona_key_score_dict[ans_id] = int(ans_attrib["Score"])
                            nona_key_score_dict = OrderedDict((ans_id, score) for ans_id, score in sorted(nona_key_score_dict.items(), key=lambda item: item[1], reverse=True))
                            for ans_id, score in nona_key_score_dict.items():
                                ans_text = BeautifulSoup(parent["NonAnswers"][ans_id]["Body"], "html.parser").get_text()
                                out_dict['non_answers'].append(ans_text)
                                out_dict['non_answers_scores'].append(score)

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
                                self.ar.add_data(
                                    filter_newlines(out_str), 
                                    meta=out_dict
                                )
                            except:
                                self.ar.add_data(
                                    filter_newlines(handle_unicode_errors(out_str)), 
                                    meta=out_dict
                                )
                        if self.sample and len(out_dict['answers'])>=3:
                            with open("{}/samples/sample_{}".format(self.out_folder, out_name), 'w') as f:
                                try:
                                    f.write(filter_newlines(out_str))
                                except:
                                    f.write(filter_newlines(handle_unicode_errors(out_str)))
                            self.sample = False
                        self.num_questions += 1
                        self.num_answers += len(out_dict['answers'])
                        if len(key_score_dict)-len(out_dict['answers'])>0:
                            self.num_discarded_answers += len(key_score_dict)-len(out_dict['answers']) # cases where number of answers is > max responses
                            print(f"Discarding {len(key_score_dict)-len(out_dict['answers'])} of {len(key_score_dict)} answers", self.num_discarded_answers)                        
                    else:
                        # discard questions with no accepted answers
                        self.num_discarded_questions += 1
        for key in keys_to_del:
            self.questions.pop(key, None)

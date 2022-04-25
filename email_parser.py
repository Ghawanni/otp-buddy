import asyncio
import datetime
from gc import garbage
import logging
from posixpath import split
from pydoc import plain
import string
from typing import List, Tuple
from email_listener import email_parser

import grpc
import email_exchange_pb2
import email_exchange_pb2_grpc

from bs4 import BeautifulSoup

import re
REGEX_DIGITS_PATTERN = '\d{4,6}'
SCORING_RANGE = 25
# add words here to increase precision
OTP_WORD_LIST = set(["login", "otp", "password",
                    "one-time", "one", "time", "code", "رمز", "دخول", "رقم", "سري", "الرقم", "الدخول", "السري", "الرمز", "مؤقت", "المؤقت", "تحقق", "التحقق"])


class EmailExchangeServicer(email_exchange_pb2_grpc.EmailExchangeServicer):
    '''EmailExchangeServicer class implement the service gRPC functions'''
    async def SendToParser(
        self, email: email_exchange_pb2.EmailParserRequest, context: grpc.aio.ServicerContext
    ) -> email_exchange_pb2.EmailParserResponse:
        '''
        @IMPLEMENTES: SendToParser
        @Params:
            self: instance of the EmailExchangeServicer class (gRPC req.)
            email: the email test received by gRPC (as defined in the gRPC service)
            context: the context of the implementation (gRPC req.)
            returns: EmailParserResponse that contains a boolean showing if email is recevied
        '''
        # print(f'Received the following email: {email.email}')
        if email.email is not None:
            email_text = email.email
            email_without_headers = clean_email_headers(email_text=email_text)
            clean_email_text = get_email_text(
                email_text=email_without_headers)
            re_otp_list = parse_email_text(clean_email_text)
            return email_exchange_pb2.EmailParserResponse(received=True)
        return email_exchange_pb2.EmailParserResponse(received=False)


def clean_email_headers(email_text: string) -> string:
    '''Take in full raw email text and returns email markup only'''
    email_without_headers = email_text.split("<!doctype html>")
    if len(email_without_headers) < 2:
        return email_text
    return email_without_headers[1]


def get_email_text(email_text: string) -> string:
    '''
    Takes in the email text with HMTML markup (no headers)
    then transforms it into plain text
    '''
    soup = BeautifulSoup(email_text, 'html.parser')
    email_text = soup.get_text()
    email_text = " ".join(email_text.split()).lower()
    print(f"Here's the soup after stripping: \n{email_text}\n\n")
    return email_text


def parse_email_text(plain_email_text: string) -> List[re.Match]:
    """_summary_

    Args:
        plain_email_text (string): _description_

    Returns:
        List[re.Match]: _description_
    """
    print(plain_email_text)
    match_list = re.finditer(REGEX_DIGITS_PATTERN, plain_email_text)
    potential_otp_list = []
    for match_entry in match_list:
        match_entry.group(0)
        # print(match_entry)
        scored_entry = score_match_entry(match_entry, plain_email_text)
        # scored_entry[0] is an re.Match obj & scored_entry[1] is the score of the re.Match obj
        if scored_entry[1] == 0:
            pass
        potential_otp_list.append(scored_entry)
    # print(f"Matched numbers from RE: {}")
    return potential_otp_list


def score_match_entry(match_entry: re.Match, plain_email_text: string) -> Tuple[re.Match, int]:
    """_summary_

    Args:
        match_entry (_type_): _description_
        int (_type_): _description_
    """
    start_index = match_entry.span()[0]
    end_index = match_entry.span()[1]
    scoring_scope = plain_email_text[start_index -
                                     SCORING_RANGE:end_index+SCORING_RANGE]
    # Make all lower case, remove duplicates and split on space for better comparison
    scoring_scope = set(scoring_scope.lower().split())
    # This line compares the length of the total scope with the length of the difference; yielding the matching score
    entry_score = len(scoring_scope) - \
        len(scoring_scope.difference(OTP_WORD_LIST))
    print(scoring_scope)
    print((match_entry, entry_score))
    return (match_entry, entry_score)


async def serve() -> None:
    '''A function instantiates a server to receive gRPC call (based on asyncio)'''
    server = grpc.aio.server()
    email_exchange_pb2_grpc.add_EmailExchangeServicer_to_server(
        EmailExchangeServicer(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())

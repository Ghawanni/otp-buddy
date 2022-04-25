import asyncio
from gc import garbage
import logging
from posixpath import split
import string
from email_listener import email_parser

import grpc
import email_exchange_pb2
import email_exchange_pb2_grpc

from bs4 import BeautifulSoup


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
            email_text= email.email
            email_without_headers = clean_email_headers(email_text=email_text)
            clean_email_text = parse_email_text(
                email_text=email_without_headers)
            return email_exchange_pb2.EmailParserResponse(received=True)
        return email_exchange_pb2.EmailParserResponse(received=False)


def clean_email_headers(email_text: string) -> string:
    '''Take in full raw email text and returns email markup only'''
    email_without_headers = email_text.split("<!doctype html>")
    
    return email_without_headers[1]


def parse_email_text(email_text: string) -> string:
    '''
    Takes in the email text with HMTML markup (no headers)
    then transforms it into plain text
    '''
    soup = BeautifulSoup(email_text, 'html.parser')
    print(f"Here's the soup: \n{soup.get_text().strip()}")
    return "yay parsed"


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

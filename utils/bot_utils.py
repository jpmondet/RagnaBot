""" Some utils used in all bot files """

#! /usr/bin/env python3

from typing import List, Dict, Any
from compute.middle_layer import check_if_registered as cml_check_if_registered

def paginate(lines: List[str], prefix: str = '```css\n', suffix: str = '```', chars=1850) -> str :
    """ Paginate long outputs since discord limits to 2000 chars... """
    size: int = 0
    message: List[str] = [prefix]
    for line in lines:
        if len(line) + size > chars:
            message.append(suffix)
            yield message
            message = [prefix]
            size = 0
        message.append(line)
        size += len(line)
    message.append(suffix)
    yield message

async def record_usage(instance, ctx):
    print(f"[{instance}] {ctx.author} asked for {ctx.message.content} on chan {ctx.channel} of {ctx.guild} at {ctx.message.created_at}")

async def check_if_registered(ctx):
    ret = cml_check_if_registered(ctx.author.id)
    print(ret)
    return ret
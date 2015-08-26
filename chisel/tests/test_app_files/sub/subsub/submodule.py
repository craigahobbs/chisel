# pylint: disable=missing-docstring

import chisel


@chisel.action(urls=('/my_action3/{myArg}',))
def my_action3(dummy_ctx, req):
    assert req['myArg'] == 123
    return {'myArg': str(req['myArg'])}

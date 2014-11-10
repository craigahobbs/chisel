import chisel

@chisel.action(urls = ('/myAction3/{myArg}',))
def myAction3(ctx, req):
    assert req['myArg'] == 123
    return {'myArg': str(req['myArg'])}

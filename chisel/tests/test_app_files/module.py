import chisel

# Action callback used by test_app.py
@chisel.action
def myAction(ctx, req):

    # Get the test resource
    with ctx.resources.testResource:
        pass

    # Log info and a warning
    ctx.log.debug('Some info')
    ctx.log.warning('A warning...')

    return {}

@chisel.action
def myAction2(ctx, req):
    ctx.log.info('In myAction2')

    with ctx.resources['myresource'] as resource:

        if 'MYENVIRON' in ctx.environ:
            multiplier = int(ctx.environ['MYENVIRON'])
        else:
            multiplier = resource

        return { 'result': req['value'] * multiplier }

@chisel.action(urls = ('/myAction3/{myArg}',))
def myAction3(ctx, req):
    assert req['myArg'] == 123
    return {'myArg': str(req['myArg'])}

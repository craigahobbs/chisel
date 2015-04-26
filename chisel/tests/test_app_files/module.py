import chisel


# Action callback used by test_app.py
@chisel.action
def myAction(ctx, req):

    # Log info and a warning
    ctx.log.debug('Some info')
    ctx.log.warning('A warning...')

    return {}


@chisel.action
def myAction2(ctx, req):
    ctx.log.info('In myAction2')

    if 'MYENVIRON' in ctx.environ:
        multiplier = int(ctx.environ['MYENVIRON'])
    else:
        multiplier = 2

    return {'result': req['value'] * multiplier}

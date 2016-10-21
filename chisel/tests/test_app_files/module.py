import chisel

# my_action3 should not load from here - will error if it does...
from .sub.subsub.submodule import my_action3 # pylint: disable=unused-import


# Action callback used by test_app.py
@chisel.action
def my_action(ctx, dummy_req):

    # Log info and a warning
    ctx.log.debug('Some info')
    ctx.log.warning('A warning...')

    return {}


@chisel.action
def my_action2(ctx, req):
    ctx.log.info('In my_action2')

    if 'MYENVIRON' in ctx.environ:
        multiplier = int(ctx.environ['MYENVIRON'])
    else:
        multiplier = 2

    return {'result': req['value'] * multiplier}


@chisel.action
def my_action4(ctx, dummy_req):
    ctx.log.info('In my_action4')

    return {'reconstructedURL': ctx.reconstructed_url or 'ERROR'}

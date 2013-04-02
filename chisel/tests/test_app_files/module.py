import chisel

# Action callback used by test_app.py
@chisel.action
def myAction(ctx, req):

    # Get the test resource
    with ctx.resources.testResource:
        pass

    # Log info and a warning
    ctx.log.debug("Some info")
    ctx.log.warning("A warning %s, %s" % (ctx.config.foo, ctx.config.bonk))

    return {}

@chisel.action
def myAction2(ctx, request):
    ctx.log.info("In myAction2")

    with ctx.resources['myresource'] as resource:

        if 'MYENVIRON' in ctx.environ:
            multiplier = int(ctx.environ['MYENVIRON'])
        else:
            multiplier = resource

        return { "result": request.value * multiplier }

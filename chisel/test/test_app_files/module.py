import chisel

# Action callback used by test_app.py
@chisel.action
def myAction(ctx, req):

    # Get the test resource
    with ctx.resources.testResource() as testResource:
        pass

    # Update the cache
    if "myAction" not in ctx.cache:
        ctx.cache.myAction = chisel.Struct(count = 0)
    ctx.cache.myAction.count += 1

    # Log info and a warning
    ctx.log.info("Some info")
    ctx.log.warning("A warning %d" % (ctx.cache.myAction.count))

    return {}

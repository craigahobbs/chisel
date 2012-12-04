import chisel

# Action callback used by test_app.py
@chisel.action
def myAction(ctx, req):

    # Get the test resource
    with ctx.resources.testResource() as testResource:
        pass

    # Update the cache
    with ctx.cache() as cache:
        if "myAction" not in cache:
            cache.myAction = chisel.Struct(count = 0)
        cache.myAction.count += 1
        count = cache.myAction.count

    # Log info and a warning
    ctx.log.info("Some info")
    ctx.log.warning("A warning %d" % (count))

    return {}

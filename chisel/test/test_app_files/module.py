import chisel

# Action callback used by test_app.py
@chisel.action
def myAction(ctx, req):

    # Get the test resource
    with ctx.resources.testResource() as testResource:
        pass

    # Log info and a warning
    ctx.log.info("Some info")
    ctx.log.warning("A warning")

    return {}

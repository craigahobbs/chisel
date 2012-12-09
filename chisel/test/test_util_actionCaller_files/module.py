import chisel

@chisel.action
def myAction(ctx, request):
    ctx.log.info("In myAction")
    with ctx.resources.myresource() as resource:
        return { "result": request.value * resource }

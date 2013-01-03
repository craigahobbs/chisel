import chisel

@chisel.action
def myAction1(ctx, request):
    return {}

@chisel.action
def myAction2(ctx, input):
    return { "c": input.a + input.b }

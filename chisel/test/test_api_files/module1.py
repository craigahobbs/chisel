def myAction1(ctx, request):
    return {}

def myAction2(ctx, input):
    return { "c": input.a + input.b }

def actions():
    return [
        myAction1,
        myAction2
        ]

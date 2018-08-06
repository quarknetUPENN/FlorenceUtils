from datareception import fmt


def printreg(reg, name=None):
    if name is not None:
        print(fmt.BOLD + name + ": " + fmt.END)
    print("+" + (3 * len(reg) - 2) * "-" + "+")
    for bit in reg:
        print(fmt.BOLD + " " + bit + "|", end="")
    print(fmt.END)
    for bitn in range(len(reg)):
        if len(str(len(reg) - 1 - bitn)) == 1:
            print(" ", end="")
        print(str(len(reg) - 1 - bitn) + "|", end="")
    print("\n+" + (3 * len(reg) - 2) * "-" + "+")


printreg("00000100011111100001110100001011")
printreg("00000000000101110001011000001011")

from datareception import *
import matplotlib.pyplot as plt

def printfdf(fname):
    with open(fname, "r") as fdf:
        data = eval(fdf.readline())
        kwargs = eval(fdf.readline())
    threshspace = kwargs["l1as_to_send"]

    channeldata = ["" for i in range(32)]
    for l1an in range(0, len(data), threshspace):
        for l1ann in range(l1an, l1an + threshspace):
            for channeln in range(len(channeldata)):
                channeldata[channeln] += (data[l1an].asdblrs[0] + data[l1an].asdblrs[47])[channeln]
    print(len(channeldata[0]))

    print("Now printing {}:".format(fname))
    for channel in channeldata:
        bitn = 0
        for char in channel:
            if bitn % (24 * threshspace) == 0:
                print(fmt.RED + "|X|" + fmt.END, end="")
            elif bitn % 24 == 0:
                print("|", end="")

            bitn += 1
            if char == "1":
                print(fmt.GREEN + char + fmt.END, end="")
            elif char == "0":
                print(fmt.BLUE + char + fmt.END, end="")
        print("")



def graphfdf(fname):
    with open(fname, "r") as fdf:
        data = eval(fdf.readline())
        kwargs = eval(fdf.readline())
    threshspace = kwargs["l1as_to_send"]

    channeldata = ["" for i in range(32)]
    for l1an in range(0, len(data), threshspace):
        for l1ann in range(l1an, l1an + threshspace):
            for channeln in range(len(channeldata)):
                channeldata[channeln] += (data[l1an].asdblrs[0] + data[l1an].asdblrs[47])[channeln]

    plotdata = []
    n = 0
    for channel in channeldata:
        threshavgs = [channel[n:n+(24*threshspace)] for n in range(0, len(channel), 24*threshspace)]
        threshavgs = [threshavg.count("1") / len(threshavg) for threshavg in threshavgs]
        if n % 16 <= 11:
            plotdata.append(threshavgs)
        n += 1

    for plotdatum in plotdata:
        plt.plot(kwargs["lowthreshs"], plotdatum)
    plt.title(fname)
    plt.xlabel("Threshold Value")
    plt.ylabel("% of received 1s")
    plt.show()


def showLastFdf(usePrint=True, useGraph=True):
    # print the last fdf saved
    with open(ZynqTCPHandler.LogFileName, "r") as log:
        try:
            lastsavedfdf = log.readlines()[-1][19:-1]
        except IndexError:
            print("Last fdf was not saved, cannot print file")
            exit()

    if lastsavedfdf[-4:] == ".fdf":
        if usePrint:
            printfdf(lastsavedfdf)
        if useGraph:
            graphfdf(lastsavedfdf)
    else:
        print("Last fdf was not saved, cannot print file \""+lastsavedfdf+"\"")

if __name__ == "__main__":
    showLastFdf(usePrint=False)

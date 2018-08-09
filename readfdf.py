from datareception import *
import matplotlib.pyplot as plt
import numpy as np

markers = ["s", "o", "<", "D", "h", "X"]
colors = [plt.cm.get_cmap("brg")(n/12) for n in range(12)]
colors = [[color[0], color[1], color[2], 1] for color in colors]


def printfdf(fname):
    with open(fname, "r") as fdf:
        kwargs = eval(fdf.readline())
        data = []
        for line in fdf.readlines():
            data.append(eval(line))
    threshspace = kwargs["l1as_to_send"]

    channeldata = ["" for i in range(32)]
    for l1an in range(0, len(data), threshspace):
        for l1ann in range(l1an, l1an + threshspace):
            for channeln in range(len(channeldata)):
                channeldata[channeln] += (data[l1an].asdblrs[0] + data[l1an].asdblrs[47])[channeln]
    print(len(channeldata[0]))

    print("Now printing {}".format(fname), end="")
    if kwargs["notes"] == "":
        print(":")
    else:
        print(", with note: " + kwargs["notes"])
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
    fdf.close()


def graphfdf(fname):
    with open(fname, "r") as fdf:
        kwargs = eval(fdf.readline())
        data = []
        for line in fdf.readlines():
            data.append(eval(line))
    threshspace = kwargs["l1as_to_send"]

    channeldata = ["" for i in range(32)]
    for l1an in range(0, len(data), threshspace):
        for l1ann in range(l1an, l1an + threshspace):
            for channeln in range(len(channeldata)):
                channeldata[channeln] += (data[l1an].asdblrs[0] + data[l1an].asdblrs[47])[channeln]

    plotdata = []
    n = 0
    for channel in channeldata:
        threshavgs = [channel[n:n + (24 * threshspace)] for n in range(0, len(channel), 24 * threshspace)]
        threshavgs = [threshavg.count("1") / len(threshavg) for threshavg in threshavgs]
        if n % 16 <= 11:
            plotdata.append(threshavgs)
        n += 1

    plotdata2 = []
    for channeln in range(len(plotdata)):
        threshset = []
        threshsetdata = []
        for threshn in range(len(plotdata[channeln])):
            thresh = kwargs["lowthreshs"][threshn]

            if thresh not in threshset:
                threshset.append(thresh)
                threshsetdata.append([])

            ind = threshset.index(thresh)
            threshsetdata[ind].append(plotdata[channeln][threshn])
        plotdata2.append([threshset, threshsetdata,
                          np.quantile(threshsetdata, 0.25, axis=1),
                          np.quantile(threshsetdata, 0.50, axis=1),
                          np.quantile(threshsetdata, 0.75, axis=1)])

    n = 0
    for channelplotdata in plotdata2:
        if n % 12 == 0:
            fig, axes = plt.subplots(3, 4)

        ax = axes[(n // 4) % 3, n % 4]

        bgn = 0
        for bgchannels in plotdata2[12*(n // 12):12*((n // 12)+1)]:
            ax.errorbar(bgchannels[0], bgchannels[3], marker=markers[bgn % len(markers)], capsize=3, ms=4, lw=2,
                        yerr=[bgchannels[3] - bgchannels[2], bgchannels[4] - bgchannels[3]],
                        color=[colors[bgn % 12][ind] if ind is not 3 else 0.2 for ind in range(len(colors[bgn % 12]))])
            bgn += 1
        ax.errorbar(channelplotdata[0], channelplotdata[3], marker=markers[n % len(markers)], capsize=3, ms=4, lw=3,
                    yerr=[channelplotdata[3] - channelplotdata[2], channelplotdata[4] - channelplotdata[3]],
                    color=tuple(colors[n % 12]), label="ch#"+str(n % 12), markeredgewidth=3)
        ax.set_xlim(min(kwargs["lowthreshs"]), max(kwargs["lowthreshs"]))
        ax.set_ylim(0, 1)

        ax.text(.5, .9, "channel "+str(n), fontsize=15, horizontalalignment="center", transform=ax.transAxes)
        if n // 4 == 2:
            ax.set_xlabel("Threshold Value")
        if n % 4 == 0:
            ax.set_ylabel("% of received 1s")

        if n % 12 == 11:
            fig.suptitle(fname + " roc#" + str((n // 12)), fontsize=40)
            fig.text(0.5, 0.9, kwargs["notes"], ha="center")
            mng = plt.get_current_fig_manager()
            mng.resize(*mng.window.maxsize())
            plt.show()
        n += 1


def showLastFdf(useprint=True, usegraph=True):
    # print the last fdf saved
    with open(ZynqTCPHandler.LogFileName, "r") as log:
        try:
            lastsavedfdf = log.readlines()[-1][19:-1]
        except IndexError:
            print("Last fdf was not saved, cannot print file")
            return

    if lastsavedfdf[-4:] == ".fdf":
        if useprint:
            printfdf(lastsavedfdf)
        if usegraph:
            graphfdf(lastsavedfdf)
    else:
        print("Last fdf was not saved, cannot print file \"" + lastsavedfdf + "\"")


if __name__ == "__main__":
    showLastFdf()

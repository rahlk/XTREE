#! /Users/rkrsn/miniconda/bin/python
from __future__ import print_function
from __future__ import division
from os import environ
from os import getcwd
from os import walk
from os import system
from pdb import set_trace
from random import uniform as rand
from random import randint as randi
from random import sample
from subprocess import call
from subprocess import PIPE
import pandas
import sys
from sklearn.tree import DecisionTreeRegressor
# Update PYTHONPATH
HOME = environ['HOME']
axe = HOME + '/git/axe/axe/'  # AXE
pystat = HOME + '/git/pystat/'  # PySTAT
cwd = getcwd()  # Current Directory
WHAT = '../SOURCE/'
sys.path.extend([axe, pystat, cwd, WHAT])
from table import clone
from sk import rdivDemo
from sk import scottknott
from smote import SMOTE
from methods1 import *
from WHAT import treatments as WHAT
from Prediction import formatData
from Prediction import CART as cart
from cliffsDelta import cliffs
from demos import cmd
from numpy import median


class predictor():

  def __init__(
          self,
          train=None,
          test=None,
          tuning=None,
          smoteit=False,
          duplicate=False):
    self.train = train
    self.test = test
    self.tuning = tuning
    self.smoteit = smoteit
    self.duplicate = duplicate

  def CART(self):
    "  CART"
    # Apply random forest Classifier to predict the number of bugs.
    if self.smoteit:
      self.train = SMOTE(
          self.train,
          atleast=50,
          atmost=101,
          resample=self.duplicate)

    if not self.tuning:
      clf = DecisionTreeRegressor()
    else:
      clf = DecisionTreeRegressor(max_depth=int(self.tunings[0]),
                                  min_samples_split=int(self.tunings[1]),
                                  min_samples_leaf=int(self.tunings[2]),
                                  max_features=float(self.tunings[3] / 100),
                                  max_leaf_nodes=int(self.tunings[4]),
                                  criterion='entropy')
    features = self.train.columns[:-2]
    klass = self.train[self.train.columns[-2]]
    # set_trace()
    clf.fit(self.train[features].astype('float32'), klass.astype('float32'))
    preds = clf.predict(
        self.test[self.test.columns[:-2]].astype('float32')).tolist()
    return preds


class fileHandler():

  def __init__(self, dir='../CPM/'):
    self.dir = dir

  def reformat(self, file, train_test=True, ttr=0.5, save=False):
    """
    Reformat the raw data to suit my other codes.
    **Already done, leave SAVE switched off!**
    """
    import csv
    fread = open(self.dir + file, 'r')
    rows = [line for line in fread]
    header = rows[0].strip().split(',')  # Get the headers
    body = [[1 if r == 'Y' else 0 if r == 'N' else r for r in row.strip().split(',')]
            for row in rows[1:]]
    if save:
      "Format the headers by prefixing '$' and '<'"
      header = ['$' + h for h in header]
      header[-1] = header[-1][0] + '<' + header[-1][1:]
      "Write Header"
      with open(file, 'w') as fwrite:
        writer = csv.writer(fwrite, delimiter=',')
        writer.writerow(header)
        for b in body:
          writer.writerow(b)
    elif train_test:
      # call(["mkdir", "./Data/" + file[:-7]], stdout=PIPE)
      with open("./Data/" + file[:-7] + '/Train.csv', 'w+') as fwrite:
        writer = csv.writer(fwrite, delimiter=',')
        train = sample(body, int(ttr * len(body)))
        writer.writerow(header)
        for b in train:
          writer.writerow(b)

      with open("./Data/" + file[:-7] + '/Test.csv', 'w+') as fwrite:
        writer = csv.writer(fwrite, delimiter=',')
        test = [b for b in body if not b in train]
        writer.writerow(header)
        for b in test:
          writer.writerow(b)
#       return header, train, test
    else:
      return header, body

  def file2pandas(self, file):
    fread = open(file, 'r')
    rows = [line for line in fread]
    head = rows[0].strip().split(',')  # Get the headers
    body = [[1 if r == 'Y' else 0 if r == 'N' else r for r in row.strip().split(',')]
            for row in rows[1:]]
    return pandas.DataFrame(body, columns=head)

  def explorer(self, name):
    files = [filenames for (
        dirpath,
        dirnames,
        filenames) in walk(self.dir)][0]
    for f in files:
      if f[:-7] == name:
        self.reformat(f)
    datasets = []
    projects = {}
    for (dirpath, dirnames, filenames) in walk(cwd + '/Data/'):
      if name in dirpath:
        datasets.append([dirpath, filenames])
    return datasets

#     return files, [self.file2pandas(dir + file) for file in files]

  def preamble(self):
    print(r"""
\documentclass{article}
\usepackage{colortbl}
\usepackage{fullpage}
\usepackage{times}
\usepackage{booktabs}
\usepackage{bigstrut}
\usepackage{subfig}
\usepackage[table]{xcolor}
\usepackage{graphicx}
\graphicspath{../_fig/}
\begin{document}
\title{text}
\maketitle
""")

  def figname(self, fSel, ext, _prune, _info):
    if ext:
      a = '_w' if fSel else ""
      b = str(int(ext * 100))
      c = "_iP(%s)" % (str(int(_info * 100))) if _prune else ""
      suffix = '_%s%s%s' % (b, a, c)
      A = ", Feature Weighting" if fSel else ""
      B = ", %s Information Pruning" % (
          str(int(_info * 100)) + r"\%") if _prune else ""
      comment = "Mutation Probability = %.2f%s%s" % (ext, A, B)
      return suffix, comment
    else:
      return "_baseline", "Baseline"

  def planner(self, train, test, fSel, ext, _prune, _info):
    train_df = formatData(train)
    test_df = formatData(test)
    actual = test_df[
        test_df.columns[-2]].astype('float32').tolist()
    before = predictor(train=train_df, test=test_df).CART()
#           set_trace()
    newTab = WHAT(
        train=None,
        test=None,
        train_df=train,
        bin=True,
        test_df=test,
        extent=ext,
        fSelect=fSel,
        far=False,
        infoPrune=_info,
        method='best',
        Prune=_prune).main()
    newTab_df = formatData(newTab)
    after = predictor(train=train_df, test=newTab_df).CART()
    return actual, before, after

  def kFoldCrossVal(self, train, fSel, ext, _prune, _info, test=None, k=5):
    acc, md, auc = [], [], []
    from random import shuffle
    if not test:
      rows = train._rows
    else:
      rows = train._rows + test._rows
#     set_trace()
    # Training, Validation data
    from sklearn.cross_validation import KFold
    kf = KFold(len(rows), n_folds=k)
    for trnI, tesI in kf:
      train, test = clone(train, rows=[
          rows[i].cells for i in trnI]), clone(train, rows=[
              rows[i].cells for i in tesI])
      train_df = formatData(train)
      test_df = formatData(test)
      actual = test_df[
          test_df.columns[-2]].astype('float32').tolist()
      before = predictor(train=train_df, test=test_df).CART()
      actual, before, after = self.planner(
          train, test, fSel, ext, _prune, _info)
      md.append(median(before) / median(after))
      auc.append(sum(before) / sum(after))
      acc.extend(
          [(1 - abs(b - a) / a) * 100 for b, a in zip(before, actual)])
    return acc, auc, md

  def crossval(self, name='Apache', k=5, fSel=True,
               ext=0.5, _prune=False, _info=0.25, method='best'):

    cv_acc = [name]
    cv_md = [name]
    cv_auc = [name]
    for _ in xrange(k):
      data = self.explorer(name)
      train = createTbl([data[0][0] + '/' + data[0][1][1]], isBin=False)
      test = createTbl([data[0][0] + '/' + data[0][1][0]], isBin=False)
      a, b, c = self.kFoldCrossVal(
          train, fSel, ext, _prune, _info, test=test, k=5)
      cv_acc.extend(a)
      cv_auc.extend(b)
      cv_md.extend(c)
    return cv_acc, cv_auc, cv_md

  def main(self, name='Apache', reps=10, fSel=True,
           ext=0.5, _prune=False, _info=0.25):
    effectSize = []
    Accuracy = []
    out_auc = []
    out_md = []
    out_acc = []

    cv_auc = []
    cv_md = []
    cv_acc = []
    for _ in xrange(reps):
      data = self.explorer(name)

      # self.preamble()
      for d in data:
        #       print("\\subsection{%s}\n \\begin{figure}\n \\centering" %
        #             (d[0].strip().split('/')[-1]))
        if name == d[0].strip().split('/')[-1]:
          #           set_trace()
          train = createTbl([d[0] + '/' + d[1][1]], isBin=False)
          test = createTbl([d[0] + '/' + d[1][0]], isBin=False)
#           if reps % 2 == 0:
#             a, b, c = self.kFoldCrossVal(train, fSel, ext, _prune, _info, k=5)
#             cv_acc.extend(a)
#             cv_md.extend(c)
#             cv_auc.extend(b)
          actual, before, after = self.planner(
              train, test, fSel, ext, _prune, _info)
          cliffsdelta = cliffs(lst1=actual, lst2=after).delta()
          out_auc.append(sum(before) / sum(after))
          out_md.append(median(before) / median(after))
          out_acc.extend(
              [(1 - abs(b - a) / a) * 100 for b, a in zip(before, actual)])
    out_auc.insert(0, name + self.figname(fSel, ext, _prune, _info)[0])
    out_md.insert(0, name + self.figname(fSel, ext, _prune, _info)[0])
    out_acc.insert(0, name)

    cv_auc.insert(0, name + ', crossval')
    cv_md.insert(0, name + ', crossval')
    cv_acc.insert(0, name + ', crossval')
    return out_acc, out_auc, out_md
    #----------- DEGUB ----------------
#     set_trace()

  def mainraw(self, name='Apache', reps=10, fSel=True,
              ext=0.5, _prune=False, _info=0.25, method='best'):
    data = self.explorer(name)
    before, after = [], []
    for _ in xrange(reps):
      for d in data:
        if name == d[0].strip().split('/')[-1]:
          train = createTbl([d[0] + '/' + d[1][1]], isBin=False)
          test = createTbl([d[0] + '/' + d[1][0]], isBin=False)
          train_df = formatData(train)
          test_df = formatData(test)
          actual = test_df[
              test_df.columns[-2]].astype('float32').tolist()
          before.append(predictor(train=train_df, test=test_df).CART())
  #           set_trace()
          newTab = WHAT(
              train=[d[0] + '/' + d[1][1]],
              test=[d[0] + '/' + d[1][0]],
              train_df=train,
              bin=True,
              test_df=test,
              extent=ext,
              fSelect=fSel,
              far=False,
              infoPrune=_info,
              method=method,
              Prune=_prune).main()
          newTab_df = formatData(newTab)
          after.append(predictor(train=train_df, test=newTab_df).CART())
    return before, after


def preamble1():
  print(r"""\documentclass{article}
    \usepackage{colortbl}
    \usepackage{fullpage}
    \usepackage{booktabs}
    \usepackage{bigstrut}
    \usepackage[table]{xcolor}
    \usepackage{picture}
    \newcommand{\quart}[4]{\begin{picture}(100,6)
    {\color{black}\put(#3,3){\circle*{4}}\put(#1,3){\line(1,0){#2}}}\end{picture}}
    \begin{document}
    """)


def postabmle():
  print(r"""
  \end{document}
  """)


def overlayCurve(
        w, x, y, z, base, fname=None, ext=None, textbox=False, string=None):
  from numpy import linspace
  import matplotlib.pyplot as plt
  import matplotlib.lines as mlines

  fname = 'Untitled' if not fname else fname
  ext = '.jpg' if not ext else ext
  fig = plt.figure()
  ax = fig.add_axes([0.1, 0.1, 0.6, 0.75])
  wlim = linspace(1, len(w[0]), len(w[0]))
  xlim = linspace(1, len(x[0]), len(x[0]))
  ylim = linspace(1, len(y[0]), len(y[0]))
  zlim = linspace(1, len(z[0]), len(z[0]))
  # plt.subplot(221)
  ax.plot(xlim, sorted(w[0]), 'r')
  ax.plot(ylim, sorted(x[0]), 'g')
  ax.plot(xlim, sorted(y[0]), 'm')
  ax.plot(ylim, sorted(z[0]), 'b')
  ax.plot(zlim, sorted(base[0]), 'k')

  # add a 'best fit' line
  ax.set_xlabel('Test Cases', size=18)
  ax.set_ylabel('Performance Scores (s)', size=18)
  plt.title(fname)
  # plt.title(r'Histogram (Median Bugs in each class)')

  # Tweak spacing to prevent clipping of ylabel
#     plt.subplots_adjust(left=0.15)
  "Legend"
  black_line = mlines.Line2D([], [], color='k', marker='*',
                             markersize=0, label='Baseline')
  blue_line = mlines.Line2D([], [], color='b', marker='*',
                            markersize=0, label=z[1])
  meg_line = mlines.Line2D([], [], color='m', marker='*',
                           markersize=0, label=y[1])
  green_line = mlines.Line2D([], [], color='g', marker='*',
                             markersize=0, label=x[1])
  red_line = mlines.Line2D([], [], color='r', marker='*',
                           markersize=0, label=w[1])
  plt.legend(
      bbox_to_anchor=(
          1.05,
          1),
      loc=2,
      borderaxespad=0.,
      handles=[black_line,
               red_line,
               blue_line,
               meg_line,
               green_line,
               ])
  if textbox:
    "Textbox"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, string, fontsize=14,
            verticalalignment='top', bbox=props)
  plt.savefig('./_fig/' + fname + ext)
  plt.close()


def _test(name='Apache'):
  Accuracy = []
#   preamble1()
#   for name in ['Apache', 'SQL', 'BDBC', 'BDBJ', 'X264', 'LLVM']:
  Gain = []
  medianDelta = []

  Gain.append(fileHandler().main(
      name=name,
      ext=0,
      _prune=False,
      _info=1,
      fSel=False)[2])

  for fSel in [True, False]:
    for ext in [0.25, 0.5, 0.75]:
      md, cv = fileHandler().main(
          name=name,
          ext=ext,
          _prune=False,
          _info=1,
          fSel=fSel)[2:3]
      medianDelta.append(md)

  for _info in [0.25, 0.5, 0.75]:
    for fSel in [True, False]:
      for ext in [0.25, 0.5, 0.75]:
        Gain.append(fileHandler().main(
            name=name,
            ext=ext,
            _prune=True,
            _info=_info,
            fSel=fSel)[2])

  for g in Gain:
    print(g)


def _doCrossVal():
  cv_acc = []
  cv_auc = []
  cv_md = []

  for name in ['Apache', 'SQL', 'BDBC', 'BDBJ', 'X264', 'LLVM']:
    a, b, c = fileHandler().crossval(name, k=5)
    cv_acc.append(a)
    cv_auc.append(b)
    cv_md.append(c)
  print(r"""\documentclass{article}
  \usepackage{colortbl}
  \usepackage{fullpage}
  \usepackage[table]{xcolor}
  \usepackage{picture}
  \newcommand{\quart}[4]{\begin{picture}(100,6)
  {\color{black}\put(#3,3){\circle*{4}}\put(#1,3){\line(1,0){#2}}}\end{picture}}
  \begin{document}
  """)
  print(r"\subsubsection*{Accuracy}")
  rdivDemo(cv_acc, isLatex=True)
  print(r"\end{tabular}")
  print(r"\subsubsection*{Area Under Curve}")
  rdivDemo(cv_auc, isLatex=True)
  print(r"\end{tabular}")
  print(r"\subsubsection*{Median Spread}")
  rdivDemo(cv_md, isLatex=True)
  print(r'''\end{tabular}
  \end{document}''')


def _testPlot(name='Apache'):
  Accuracy = []
#  fileHandler().preamble()
  figname = fileHandler().figname
#   for name in ['Apache', 'SQL', 'BDBC', 'BDBJ', 'X264', 'LLVM']:
#     print("\\subsection{%s}\n \\begin{figure}\n \\centering" % (name))
  before, baseline = fileHandler().mainraw(
      name=name,
      ext=0,
      _prune=False,
      _info=1,
      fSel=False)

  _, best1 = fileHandler().mainraw(
      name=name,
      method='mean',
      ext=0.75,
      _prune=True,
      _info=0.25,
      fSel=False)

  _, best2 = fileHandler().mainraw(
      name=name,
      ext=0.75,
      method='median',
      _prune=True,
      _info=0.25,
      fSel=False)

  _, best3 = fileHandler().mainraw(
      name=name,
      ext=0.75,
      method='any',
      _prune=True,
      _info=0.25,
      fSel=False)

  _, best4 = fileHandler().mainraw(
      name=name,
      ext=0.75,
      method='best',
      _prune=True,
      _info=0.25,
      fSel=False)
  print("Baseline,mean,median,any,best")
  for b, me, md, an, be in zip(baseline[0], best1[0], best2[0], best3[0], best4[0]):
    print("%0.2f,%0.2f,%0.2f,%0.2f,%0.2f" % (b, me, md, an, be))
#     overlayCurve([best1[0], 'mean'],
#                  [best2[0], 'median'],
#                  [best3[0], 'random'],
#                  [best4[0], 'best'],
#                  [baseline[0], 'baseline'],
#                  fname=name,
#                  ext='.jpg',
#                  textbox=False,
#                  string=None)
#     print(
#         "\\subfloat[][]{\\includegraphics[width=0.5\\linewidth]{../_fig/%s}\\label{}}" %
#         (name + '.jpg'))
#     print(r"\end{figure}")
#   print(r"\end{document}")

if __name__ == '__main__':
  _doCrossVal()

# my libs
from lib.jr import jrfuncs, jrdfuncs, jrauxfuncs
from lib.jr.jrfuncs import jrprint
from lib.jr.jrfilefinder import JrFileFinder


# casebook stuff
#
from .jrinterp import JrInterpreter
#
from .cbtags import CbTagManager, CbCheckboxManager
#
from .cbquestions import CbQuestionManager

from .cbdays import CbDayManager
from .cbmindmanagergv import CbMindManagerGv
#
from lib.casebook.cbtasks import CbTaskLatex, CbTaskFastParseGameInfo, CbTaskZipFiles
#
from lib.casebook.cbhelpers import createHtmlFromCbSourceFile, fastKludgeParseGameInfoFromFile, fastKludgeParseGameSettingsFromText
from .casebookDefines import *

# ast modules
from . import jrastcbr
from .jrastutilclasses import JrINote

# hlapi
from lib.hlapi import hlapi


# python
import os
import json






# main class
class JrInterpreterCasebook(JrInterpreter):
    def __init__(self, debugMode, expectSubdirectoriesForLocalMediaFiles):
        super().__init__(debugMode)

        self.sharedMediaDirectory = None

        # subclass options
        self.reportMode = True

        # subdirectories for localMediaFiles (with django this is false)
        self.expectSubdirectoriesForLocalMediaFiles = expectSubdirectoriesForLocalMediaFiles

        # create helper data structures
        self.createRenderDataStructures()

        # fileManagers (not recreated on render)
        self.fileManagers = {}

        # create derived root
        self.ast = self.createRootAst()


    def createRenderDataStructures(self):
        # create/clear any data before rendering
        # this is called BOTH at creation, AND before any render, in order to clear the contents of these
        # ATTN: TODO -- instead of relying on garbage collection on recreation of these we could implement clearing functions for them

        # hlapi (data manage for leads)
        self.hlapi = hlapi.HlApi(None, {})
        self.hlapiPrev = hlapi.HlApi(None, {})
       
        # tag manager, checkbox manager
        self.tagManager = CbTagManager()
        self.conceptManager = CbTagManager()
        self.checkboxManager = CbCheckboxManager()

        # day manager
        self.dayManager = CbDayManager()
        # mind manager
        self.mindManager = CbMindManagerGv()

        # question manage
        self.questionManager = CbQuestionManager()


    def resetRenderDataStructures(self, env):
        # create/clear any data before rendering
        # this is called BOTH at creation, AND before any render, in order to clear the contents of these
        # ATTN: TODO -- instead of relying on garbage collection on recreation of these we could implement clearing functions for them
        self.createRenderDataStructures()
        #
        # this is a bit kludgey, we want to keep the file managers on re-rendering, but reset use counts for any reports
        for key, val in self.fileManagers.items():
            # kludge to not reset count of source includes since they don't rerun on render
            if (key in [DefFileManagerNameSourceCase, DefFileManagerNameSourceShared]):
                continue
            val.resetUsageCount()


    def resetDataForRender(self, env):
        # clear any data before rendering
        self.resetRenderDataStructures(env)
        self.preBuildPreRender(env)


    def getFingerprintImageDirectoryPath(self):
        hlApi = self.getHlApi()
        return hlApi.getFingerprintImageDirectoryPath()

    


    def setupMediaDirectories(self, sharedMediaDirectory, localMediaDirectory):
        # now setup file managers
        # ATTN: new convert to abs paths
        if (sharedMediaDirectory is not None):
            sharedMediaDirectory = os.path.abspath(sharedMediaDirectory)
            sharedMediaDirectory = sharedMediaDirectory.replace("\\","/")
        if (localMediaDirectory is not None):
            localMediaDirectory = os.path.abspath(localMediaDirectory)
            localMediaDirectory = localMediaDirectory.replace("\\","/")
        #
        super().setupMediaDirectories(sharedMediaDirectory, localMediaDirectory)
        self.setupMediaFileManagers(sharedMediaDirectory, localMediaDirectory)



    def createRootAst(self):
        env = self.getEnvironment()
        #
        rootCbrAst = jrastcbr.JrAstRootCbr(self)
        #
        # setup built-in vars
        rootCbrAst.setupBuiltInVars(env)
        # setup built-in core functions
        rootCbrAst.loadCoreFunctions(env)
        # setup built-in plugins
        rootCbrAst.loadCorePlugins(self, env)
        #
        return rootCbrAst




    def convertParseTreeToAst(self):
        env = self.getEnvironment()
        # convert parse tree to our AST
        parseTree = self.jrparser.getParseTree()
        self.ast.convertParseTreeToAst(env, parseTree)
        return self.ast



    def printDebug(self, env):
        jrprint("Created Abstract Syntax Tree (AST):")
        self.ast.printDebug(env, 1)


    def taskRenderRun(self, env, task, flagFullRender):
        # just pass it off to the ast
        if (self.getDebugMode()):
            jrprint("RunRendering task '{}'..".format(task.getTaskId()))
        #
        self.ast.taskRenderRun(env, task, flagFullRender)


    def getHlApi(self):
        return self.hlapi
    def getHlApiPrev(self):
        return self.hlapiPrev
    
    def getTagManager(self):
        return self.tagManager
    def getConceptManager(self):
        return self.conceptManager


    def getCheckboxManager(self):
        return self.checkboxManager

    def getQuestionManager(self):
        return self.questionManager

    def getBuildString(self):
        return DefCbBuildString




    def setupMediaFileManagers(self, sharedMediaDirectory, localMediaDirectory):
        # create file managers

        # casebook image file manager
        if (localMediaDirectory is not None):
            imageFileManagerCase = self.setupFileManagerImages(self.addExpectSubdirectoriesForLocalMediaFiles(localMediaDirectory,"images"), "local case images", "local")
            self.setFileManager(DefFileManagerNameImagesCase, imageFileManagerCase)

        # shared image file manager
        if (sharedMediaDirectory is not None):
            fingerprintImagePath = self.getFingerprintImageDirectoryPath()
            paths = [sharedMediaDirectory + "/images", fingerprintImagePath]
            imageFileManagerShared = self.setupFileManagerImages(paths, "shared images", "shared")
            self.setFileManager(DefFileManagerNameImagesShared, imageFileManagerShared)

        # pdfs for inclusion
        if (localMediaDirectory is not None):
            pdfFileManagerCase = self.setupFileManagerPdfs(self.addExpectSubdirectoriesForLocalMediaFiles(localMediaDirectory,"pdfs"), "local case pdfs", "local")
            self.setFileManager(DefFileManagerNamePdfsCase, pdfFileManagerCase)

        # shared image file manager
        if (sharedMediaDirectory is not None):
            pdfFileManagerShared = self.setupFileManagerPdfs(sharedMediaDirectory + "/pdfs", "shared images", "shared")
            self.setFileManager(DefFileManagerNamePdfsShared, pdfFileManagerShared)

        # shared image file manager
        if (sharedMediaDirectory is not None):
            fontFileManagerShared = self.setupFileManagerFonts(sharedMediaDirectory + "/fonts", "shared fonts", "shared")
            self.setFileManager(DefFileManagerNameFontsShared, fontFileManagerShared)

        # source code includes
        sourceFileManagerList = []
        if (localMediaDirectory is not None):
            sourceFileManagerCase = self.setupFileManagerGeneric(self.addExpectSubdirectoriesForLocalMediaFiles(localMediaDirectory,"source"), [".casebook"], "local case casebook source files", "local")
            sourceFileManagerList.append(sourceFileManagerCase)
            self.setFileManager(DefFileManagerNameSourceCase, sourceFileManagerCase)

        if (sharedMediaDirectory is not None):
            sourceFileManagerShared = self.setupFileManagerGeneric(sharedMediaDirectory + "/source", [".casebook"], "shared casebook source files", "shared")
            self.setFileManager(DefFileManagerNameSourceShared, sourceFileManagerShared)
            sourceFileManagerList.append(sourceFileManagerShared)
        #
        # give deep source the file managers for including
        self.deepSource.setIncludeFileManagers(sourceFileManagerList)


    def addExpectSubdirectoriesForLocalMediaFiles(self, localMediaDirectory, suffix):
        if (self.expectSubdirectoriesForLocalMediaFiles):
            return localMediaDirectory + "/" + suffix
        else:
            return localMediaDirectory


    def setupFileManagerImages(self, paths, sourceLabel, locationClass):
        fileManagerOptions = {"stripExtensions": False}
        fileManager = JrFileFinder(fileManagerOptions, sourceLabel, locationClass)
        fileManager.clearExtensionList()
        fileManager.addExtensionListImages()
        # now scan
        directoryList = []
        # add uploads directory for this game
        if (isinstance(paths,str)):
            paths = [paths]
        for path in paths:
            directoryList.append({'prefix':'', 'path':path})
        #
        fileManager.setDirectoryList(directoryList)
        fileManager.scanDirs(False)
        #
        return fileManager


    def setupFileManagerPdfs(self, path, sourceLabel, locationClass):
        fileManagerOptions = {"stripExtensions": False}
        fileManager = JrFileFinder(fileManagerOptions, sourceLabel, locationClass)
        fileManager.clearExtensionList()
        addList = [".pdf"]
        fileManager.addExtensionList(addList)
        fileManager.addExtensionListImages()
        # now scan
        directoryList = []
        # add uploads directory for this game
        directoryList.append({'prefix':'', 'path':path})
        #
        fileManager.setDirectoryList(directoryList)
        fileManager.scanDirs(False)
        #
        return fileManager


    def setupFileManagerFonts(self, path, sourceLabel, locationClass):
        extensionList = [".ttf", ".otf"]
        return self.setupFileManagerGeneric(path, extensionList, sourceLabel, locationClass)


    def setupFileManagerGeneric(self, path, extensionList, sourceLabel, locationClass):
        fileManagerOptions = {"stripExtensions": False}
        fileManager = JrFileFinder(fileManagerOptions, sourceLabel, locationClass)
        fileManager.clearExtensionList()
        fileManager.addExtensionList(extensionList)
        # now scan
        directoryList = []
        # add uploads directory for this game
        directoryList.append({'prefix':'', 'path':path})
        #
        fileManager.setDirectoryList(directoryList)
        fileManager.scanDirs(False)
        #
        return fileManager




    def setFileManager(self, fileManagerTypeStr, fileManager):
        self.fileManagers[fileManagerTypeStr] = fileManager
        
    def getFileManager(self, fileManagerTypeStr):
        if (fileManagerTypeStr in self.fileManagers):
            return self.fileManagers[fileManagerTypeStr]
        return None


    def getSharedMediaDirectory(self):
        return self.sharedMediaDirectory
    def setSharedMediaDirectory(self, val):
        self.sharedMediaDirectory = val



    def getDayManager(self):
        return self.dayManager

    def getMindManager(self):
        return self.mindManager











    def runJobTask(self, env, job, taskName, taskOptions):
        label = jrfuncs.getDictValueOrDefault(taskOptions, "label", "anonymous")
        runTimer = jrfuncs.JrPerfTimer("Task '{}/{}'".format(label, taskName), self.getDebugMode())
        if (taskName == "latexBuildPdf"):
            [retv, task] = self.runJobTask_latexBuildPdf(env, job, taskName, taskOptions)
        elif (taskName == "fastParseGameInfo"):
            [retv, task] = self.runJobTask_fastParseGameInfo(env, job, taskName, taskOptions)
        elif (taskName == "zipFiles"):
            [retv, task] = self.runJobTask_zipFiles(env, job, taskName, taskOptions)
        else:
            msg = "Unknown casebookInterpretter task name '{}'".format(taskName)
            raise Exception(msg)
        if (self.getDebugMode()):
            runTimer.printElapsedTime()
        return retv




    def runJobTask_latexBuildPdf(self, env, job, taskName, taskOptions):
        # create task
        task = CbTaskLatex(self, taskOptions)
       
        # get options which be passed in with taskOptions or fall back to task defaults
        suffixedOutputPath = task.calcMakeSuffixedOutputDirectory()
        baseFileName = task.calcBaseFileName()
        suffixedBaseFileName = task.calcSuffixedBaseFileName()
        # not render specific but task specific
        taskGenerateMindMap = task.getOption("taskGenerateMindMap")
        taskSaveLeadJsons = task.getOption("taskSaveLeadJsons")
        taskSaveHtmlSource = task.getOption("taskSaveHtmlSource")
        taskSavePlayManifest = task.getOption("taskSavePlayManifest")
        taskSavePlainText = taskSaveHtmlSource
        taskZipFiles = task.getOption("taskZipFiles")
        cleanExtras = task.getOption("cleanExtras")
        variant = task.getOption("variant")
        convert = task.getOption("convert")
        convertSuffix = task.getOption("convertSuffix")
        #
        convertDpi = 150

        # delete all files in target directory? that is too risky; but we do want to delete all old versioned zip files
        # ATTN: this should be done in higher level TASK not on each job, OR when being asked to zip files
        if (taskZipFiles):
            jrfuncs.deleteFilePattern(suffixedOutputPath, baseFileName+"*.zip")

        # TASK EXTRAS - EARLY
        if (taskSavePlainText):
            # save the actual plain text for the record
            parserOptions = jrfuncs.getDictValueOrDefault(job, "parserOptions", None)
            sourceFilePath = jrfuncs.getDictValueOrDefault(parserOptions, "sourceFilePath", None)
            sourceFileText = jrfuncs.getDictValueOrDefault(parserOptions, "sourceFileText", None)
            outFilePath = suffixedOutputPath + "/" + baseFileName + "_casebookSource.txt"
            #
            encoding = "utf-8"
            retv = jrfuncs.saveTxtToFile(outFilePath, sourceFileText, encoding)


        # generic render run (this may set options that OVERRIDE our taskOptions, but they will ve set again by the task when we renderToPdf)
        self.taskRenderRun(env, task, True)

        # create pdf
        renderSectionName = None
        # experimental, only render specific section
        if (variant == "cover"):
            renderSectionName = "COVER"

        #
        [retv, fileList] = task.renderToPdf(suffixedOutputPath, suffixedBaseFileName, self.getDebugMode(), renderSectionName)
        if (retv):
            # success

            # TASK EXTRAS - LATE

            # save html version (note we do this late now so that we have proper hlapi loaded)
            if (taskSaveHtmlSource):
                # higher level parser options
                parserOptions = jrfuncs.getDictValueOrDefault(job, "parserOptions", None)
                sourceFilePath = jrfuncs.getDictValueOrDefault(parserOptions, "sourceFilePath", None)
                sourceFileText = jrfuncs.getDictValueOrDefault(parserOptions, "sourceFileText", None)
                #
                retv = self.saveHtmlSource(task, sourceFilePath, sourceFileText, suffixedOutputPath, baseFileName)

            # save html version (note we do this late now so that we have proper hlapi loaded)
            if (taskSavePlayManifest):
                # higher level parser options
                parserOptions = jrfuncs.getDictValueOrDefault(job, "parserOptions", None)
                sourceFilePath = jrfuncs.getDictValueOrDefault(parserOptions, "sourceFilePath", None)
                #
                retv = self.savePlayManifest(task, sourceFilePath, suffixedOutputPath, suffixedBaseFileName, baseFileName, fileList)


            if (convert is not None) and (convert != ""):
                # NOT IMPLEMENTED YET
                # convert the fileList[0] output file to an image .convertPdfToImage?
                for filePath in fileList:
                    if (not filePath.lower().endswith(".pdf")):
                        continue
                    # add suffix?
                    if (convertSuffix is not None) and (convertSuffix!=""):
                        convertedFileName = jrfuncs.addSuffixToPath(filePath, convertSuffix)
                    else:
                        convertedFileName = filePath
                    convertedFileName = jrfuncs.changeFileExtension(convertedFileName, convert)
                    #
                    if (convertedFileName != filePath):
                        # do the image conversion
                        retv = jrauxfuncs.convertPdfFileToImageFile(filePath, convertedFileName, convert, convertDpi)
                        if (retv):
                            # remove previous, add new
                            if (False):
                                self.removeGeneratedFile(filePath)
                            self.addGeneratedFile(convertedFileName)
                            if (True):
                                # only the first file gets created
                                break
                        else:
                            raise Exception("In runJobTask_latexBuildPdf, failed to convert '{}' to '{}'.".format(filePath, convertedFileName))

            # mindmap
            if (taskGenerateMindMap):
                #[retv, generatedFileName] = self.mindManager.buildMindMap(self.getEnvironment(), suffixedOutputPath, baseFileName, self.getDebugMode())
                [retv, generatedFileName] = self.mindManager.buildMindMap(env, suffixedOutputPath, baseFileName, self.getDebugMode())
                if (retv):
                    self.addGeneratedFile(generatedFileName)

            # json export of used leads
            if (taskSaveLeadJsons):
                self.saveLeadJsons(task, suffixedOutputPath, baseFileName)

            # zip?
            if (taskZipFiles):
                # ATTN: we now handle zip files mostly using a separate TASK and do NOT use this
                # add version suffix
                gameVersionStrSuffix = env.calcSafeGameVersionStr()
                if (gameVersionStrSuffix!=""):
                    gameVersionStrSuffix = "_"+gameVersionStrSuffix
                [retv, zipFilePath] = jrfuncs.zipFileList(self.getGeneratedFileListForZip(), suffixedOutputPath, suffixedBaseFileName+gameVersionStrSuffix, True, self.getDebugMode())
                self.clearGeneratedFileListForZip()
                if (retv):
                    self.addGeneratedFile(zipFilePath, False)

        # done
        return [retv, task]








    def runJobTask_zipFiles(self, env, job, taskName, taskOptions):
        # create task
        task = CbTaskZipFiles(self, taskOptions)
       
        # get options which be passed in with taskOptions or fall back to task defaults
        suffixedOutputPath = task.calcMakeSuffixedOutputDirectory()
        baseFileName = task.calcBaseFileName()
        suffixedBaseFileName = task.calcSuffixedBaseFileName()

        # add version suffix
        gameVersionStrSuffix = env.calcSafeGameVersionStr()
        if (gameVersionStrSuffix!=""):
            gameVersionStrSuffix = "_"+gameVersionStrSuffix
        [retv, zipFilePath] = jrfuncs.zipFileList(self.getGeneratedFileListForZip(), suffixedOutputPath, suffixedBaseFileName+gameVersionStrSuffix, True, self.getDebugMode())
        self.clearGeneratedFileListForZip()
        if (retv):
            self.addGeneratedFile(zipFilePath, False)

        # done
        return [retv, task]







    def runJobTask_fastParseGameInfo(self, env, job, taskName, taskOptions):
        # create task
        task = CbTaskFastParseGameInfo(self, taskOptions)
        #
        optionTryFastKludgeParseInfo = True

        if (optionTryFastKludgeParseInfo):
            # higher level parser options
            parserOptions = jrfuncs.getDictValueOrDefault(job, "parserOptions", None)
            sourceFilePath = jrfuncs.getDictValueOrDefault(parserOptions, "sourceFilePath", None)
            sourceFileText = jrfuncs.getDictValueOrDefault(parserOptions, "sourceFileText", None)
            #
            errorList = []
            if (sourceFilePath is not None):
                settings = fastKludgeParseGameInfoFromFile(sourceFilePath, "utf-8", errorList)
            else:
                settings = fastKludgeParseGameSettingsFromText(sourceFileText, errorList)
        else:
            settings = None

        if (settings is not None):
            # good enough, set from kludge parse
            info = env.getEnvValueUnwrapped(None, "info", None)
            jrfuncs.deepMergeOverwriteA(info, settings["info"])
            jrfuncs.deepMergeOverwriteA(info, settings["summary"])
            jrfuncs.deepMergeOverwriteA(info, settings["infoExtra"])
        else:
            # we require full parse
            self.addWarning("Fast kludge parse of source file for $configureGameInfo(...) was unsuccessful, so performing full slower parse..")
            self.runJobEarlyGenericsParser(job)
            # we have to parse to get info
            # generic render run (this may set options that OVERRIDE our taskOptions, but they will ve set again by the task when we renderToPdf)
            self.taskRenderRun(env, task, False)

        # generic render run (this may set options that OVERRIDE our taskOptions, but they will ve set again by the task when we renderToPdf)
        if (self.getDebugMode()):
            task.debugPrint()

        return [True, task]
























    def saveLeadJsons(self, task, outputPath, baseFilename):
        hlapi = self.getHlApi()
        forceSourceLabel = baseFilename
        #
        if (self.getDebugMode()):
            jrprint("Saving json leads..")
        savedFiles = hlapi.writeOutUsedLeadJsons(outputPath, baseFilename, forceSourceLabel)
        for savedFile in savedFiles:
            self.addGeneratedFile(savedFile)


    def saveHtmlSource(self, task, sourceFilePath, sourceFileText, outputPath, baseFilename):
        jrfuncs.createDirIfMissing(outputPath)
        outFileName = baseFilename + "_casebookSource.html"
        outFilePath = outputPath + "/" + outFileName
        retv = createHtmlFromCbSourceFile(self.hlapi, self.hlapiPrev, sourceFilePath, sourceFileText, outFilePath, self.getDebugMode())
        self.addGeneratedFile(outFilePath)
        return retv











    def savePlayManifest(self, task, sourceFilePath, outputPath, suffixedBaseFileName, baseFilename, fileList):
        # new attempt to create a nice json game play manifest
        playManifest = {}

        # walk all rendered items and add their info
        # ATTN: TODO
        env = self.getEnvironment()
        renderer = env.getRenderer()

        # leads
        playManifestLeads = []
        self.flatAddRenderedPlayManifestFromRenderItem(env, renderer, renderer, playManifestLeads, None, "")
        playManifest["leads"] = playManifestLeads

        # days with required tags
        playDays = []
        dayManager = env.getDayManager()
        tagManager = env.getTagManager()
        # iterate each day
        for key, day in dayManager.getDayDict().items():
            dayNumber = day.getDayNumber()
            dayInfo = {
                "number": dayNumber,
                "date": day.getDate().isoformat(),
                "timeStart": day.startTime,
                "timeEnd": day.endTime,
            }
            #
            # now iterate all tags with this day deadline
            requiredTags = []
            tagList = tagManager.findDeadlineTags(dayNumber)
            tagList = tagManager.sortByTypeAndObfuscatedLabel(tagList, env, True)
            if (len(tagList)>0):
                for tag in tagList:
                    # create link from day to tag for deadline
                    tagInfo = {
                        "id": tag.getId(),
                        "obfuscatedLabel": tag.getNiceObfuscatedLabelWithType(True, False),
                        "niceLabel": tag.getNiceIdWithLabel(),
                    }
                    requiredTags.append(tagInfo)
            dayInfo["deadlinedTags"] = requiredTags
            # add it
            playDays.append(dayInfo)
        playManifest["days"]  = playDays

        # tags
        tagInfos = {}
        tagManager = env.getTagManager()
        tagList = tagManager.getTagList()
        tagList = tagManager.sortByTypeAndObfuscatedLabel(tagList, env, True)
        for tag in tagList:
            id = tag.getId()
            tagInfo = {
                #"id": tag.getId(),
                "label": tag.getLabel(),
                "obfuscatedLabel": tag.getNiceObfuscatedLabelWithType(True, False),
                "deadline": tag.getDeadline()
            }
            gainList = tag.getGainList(True, True)
            checkedList = tag.getCheckList(True, True)
            tagInfo["leadsGain"] = gainList
            tagInfo["leadsCheck"] = checkedList
            tagInfos[id] = tagInfo
        playManifest["tags"] = tagInfos

        # checkboxes
        checkBoxTypes = {}
        checkboxManager = env.getCheckboxManager()
        checkmarks = checkboxManager.getCheckmarks()
        for key, checkmark in checkmarks.items():
            checkmarkTypeName = checkmark.getTypeName()
            checkmarkUses = checkmark.getUses()
            if (len(checkmarkUses)==0):
                pass
            else:
                for checkmarkUse in checkmarkUses:
                    lead = checkmarkUse["lead"]
                    if (lead is not None):
                        leadref = lead.getIdPreferAutoId()
                        markCount = checkmarkUse["count"]
                        if (not key in checkBoxTypes):
                            checkBoxTypes[key] = {}
                        if (not leadref in checkBoxTypes[key]):
                            checkBoxTypes[key][leadref] = markCount
                        else:
                            checkBoxTypes[key][leadref] += markCount
        playManifest["checkboxes"] = checkBoxTypes

        # game meta info
        gameInfo = env.getEnvValueUnwrapped(None, "info", None)
        playManifest["gameInfo"] = gameInfo

        # build info
        buildInfo = {}
        buildInfo["buildToolVersion"] = DefCbVersion
        buildInfo["buildToolDate"]= DefCbVersionDate
        buildInfo["buildStr"] = env.getBuildString()
        buildInfo["typesetStr"] = env.getTypesetString(True)
        buildInfo["currentDate"] = jrfuncs.getCurrentDateTimeUtcInIsoFormat()
        buildInfo["currentDateStr"] = jrfuncs.getNiceCurrentDateTime()   
        playManifest["buildInfo"] = buildInfo

        # stats
        gameStats = renderer.calcStatsAsDict(env)
        playManifest["stats"] = gameStats

        # new, scan generated pdf for table of contents
        pdfFilePath = self.extractPdfPathFromFileList(fileList)
        if (pdfFilePath is not None):
            pdfInfo = self.extractPdfInfoAndToc(env, task, pdfFilePath)
        playManifest["pdfInfo"] = pdfInfo


        # write file
        outFileName = baseFilename + "_playManifest.json"
        outFilePath = outputPath + "/" + outFileName
        #jrfuncs.createDirIfMissing(outputPath)
        jsonText = json.dumps(playManifest, indent=4)
        jrfuncs.saveTxtToFile(outFilePath, jsonText, "utf-8")

        return True


    def extractPdfPathFromFileList(self, fileList):
        for filePath in fileList:
            if (filePath.lower().endswith(".pdf")):
                return filePath
        return None








    def flatAddRenderedPlayManifestFromRenderItem(self, env, renderer, renderItem, playManifestLeads, parentItem, parentTocTitle):
        # add this render item
        id = renderItem.getId()
        if (id == JrCbMainSectionName_Report):
            # we dont add render section since this may be filled with stuff we dont want in play manifest
            return
        renderedInfo = renderItem.getRenderedInfo()
        #
        if (not renderedInfo is None) and (len(renderedInfo)>0):
            # ADD MORE STUFF
            #
            # add parent TOC
            tocSection = renderedInfo["toc"]
            tocSection["parentTitle"] = parentTocTitle
            playManifestLeads.append(renderedInfo)
            if ("title" in tocSection):
                parentTocTitle = tocSection["title"]
            else:
                parentToc = ""
            # add time
            timeDuration = renderer.calculateItemTime(env, renderItem, parentItem)
            renderedInfo["timeDuration"] = timeDuration if (timeDuration != False) else 0
            # continued from?
            lead = renderItem.getInlinedFromLead()
            if (lead is not None):
                lead = lead.getIdPreferAutoId()
            renderedInfo["inlinedFromLead"] = lead
            lead = renderItem.getContinuedFromLead()
            #if (lead is not None):
            #    lead = lead.getIdPreferAutoId()
            renderedInfo["continuedFromLead"] = lead
            # role?
            role = renderItem.getRole()
            if (not role is None):
                role = role.copy()
                if ("tag" in role):
                    tag = role["tag"]
                    if (tag is not None):
                        role["tag"] = role["tag"].getId()
            renderedInfo["role"] = role
            representsTag = renderItem.calcTagRepresentedByLead(env)
            if (not representsTag is None):
                representsTag = representsTag.getId()
            renderedInfo["representsTag"] = representsTag
            #
        else:
            parentToc = ""
        # add its's children
        childManagerChildren = renderItem.children
        for child in childManagerChildren.children:
            self.flatAddRenderedPlayManifestFromRenderItem(env, renderer, child, playManifestLeads, renderItem, parentTocTitle)






    def extractPdfInfoAndToc(self, env, task, pdfFilePath):
        pdfInfo = {}

        # parth to file
        pdfFileName = os.path.basename(pdfFilePath)
        pdfInfo["pdfFileName"] = pdfFileName

        # url -- this isnt really helpful since it links to the DRAFT build instead of the published build..
        absoluteUrlBase = task.getOption("absoluteUrlBase",None)
        url = absoluteUrlBase + "/" + pdfFileName
        pdfInfo["pdfUrl"] = url
        

        # use pypdf2 to grab table of contents (bookmarks) with page numbers
        from PyPDF2 import PdfReader, PdfWriter

        # helper function from chatgpt
        def get_pdf_table_of_contents(reader):
            outlines = reader.outline
            toc = []
            def process_outlines(outlines, level=0):
                for item in outlines:
                    if isinstance(item, list):
                        # Recursively process nested outlines
                        process_outlines(item, level + 1)
                    else:
                        title = item.title if hasattr(item, 'title') else str(item)
                        try:
                            page_number = reader.get_destination_page_number(item) + 1  # Pages are zero-indexed
                        except Exception:
                            page_number = None
                        toc.append({"title": title,
                                    "pageNumber": page_number,
                                    "level": level
                                    })

            process_outlines(outlines)
            return toc

        # open read
        reader = PdfReader(pdfFilePath)

        # total page count
        pdfInfo["pageCount"] = len(reader.pages)
        pdfInfo["metadata"] = reader.metadata
        #pdfInfo["xmp_metadata"] = reader.xmp_metadata

        # get toc
        toc_items = get_pdf_table_of_contents(reader)
        pdfInfo["toc"] = toc_items

        return pdfInfo

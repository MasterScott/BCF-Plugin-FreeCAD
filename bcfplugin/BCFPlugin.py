import sys
import util

def setup():
    help_str = """
This module lets you to operate on BCF files. Therefore multiple modules
can be imported:
    - bcf.reader: lets you read in the desired BCF file. Most important function
      here is: bcf.reader.readBcfFile(absolutePathToFile: str) -> Project
      The returned object is of greatest importance since you want to operate on
      it.
    - bcf.writer: lets you write out the contents of an object of type `Project`
      to the desired path. Most important function is:
      bcf.writer.addUpdate(project: Project, element, prevVal)

The internal data structure implements interfaces that make it easy to operate
on a project. So have a look into ./interfaces if you are interested.
TODO: add documentation on the interfaces part.
            """
    #print(help_str)
    if not check_dependencies():
        return

    import frontend.programmaticInterface as plugin

    project = plugin.openProject("./bcf/test_data/Issues_BIMcollab_Example.bcf.original")
    topics = plugin.getTopics()
    a = lambda x: x[1].index
    util.printInfo([ a(topic) for topic in topics ])

    viewpoints = plugin.getViewpoints(topics[0][1])
    util.printInfo(viewpoints)

    comments = plugin.getComments(topics[0][1], viewpoints[0][1])
    util.printInfo(comments)

    files = list()
    for (topicUUID, topic) in topics:
        files.append(plugin.getRelevantIfcFiles(topic))
    util.printInfo(files)


"""
If run in the command line a little help shall be printed on what the user is
able to do and how.
"""
if __name__ == "__main__":
    setup()

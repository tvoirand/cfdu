"""
Curses FTP Drive Usage main script.
"""

# standard import
import os
import curses
import ftplib
import argparse

# local imports
from user_interface import user_interface
from directory_tree import MyFile
from directory_tree import MyFolder


def scan_ftp_folder(ftp, ftp_path, parent="root"):
    """
    Recursively scan folder on FTP server, computing size of each children.
    Input:
        -ftp                    ftplib.FTP instance
        -ftp_path               str
            path of folder to scan on FTP server
        -parent                 MyFolder instance or "root"
    Return:
        -folder                 MyFolder instance
    """

    # initiate folder
    total_size = 0
    folder = MyFolder(os.path.basename(ftp_path), parent=parent)

    # get list of contents
    contents_list = ftp.nlst(ftp_path)

    # loop through each element
    for element in contents_list:

        # display scanning status to user
        progress_string = "\rScanning: {}".format(os.path.join(ftp_path, element))
        width = int(os.popen("stty size", "r").read().split()[1])  # get terminal width
        progress_string = progress_string.ljust(width)[: width - 2] # adjust display
        print(progress_string, end="", flush=True)

        try: # subfolder case

            # if we can CD to this element, it's a subfolder
            ftp.cwd(os.path.join(ftp_path, element))

            # scan subfolder
            subfolder = scan_ftp_folder(
                ftp, os.path.join(ftp_path, element), parent=folder,
            )

            # cd back to current folder
            ftp.cwd(ftp_path)

            # add size of subfolder to this folder's tree_size
            folder.size += subfolder.size

            # add subfolder to this folder's children
            folder.children.append(subfolder)

        except: # file case

            # get file size
            ftp.voidcmd(
                "TYPE I"
            )  # avoid ftplib.error_perm: 550 SIZE not allowed in ASCII mode
            file_size = ftp.size(os.path.join(ftp_path, element))

            # add size of file to this folder's size
            folder.size += file_size

            # add new file to this folder's children
            folder.children.append(
                MyFile(element, parent=folder, size=file_size)
            )

    return folder


def main(host, user, pwd):
    """
    Curses FTP Drive Usage main function.
    Input:
        -host   str
        -user   str
        -pwd    str
    """

    # connect to ftp server
    ftp = ftplib.FTP(host, user, pwd)

    # initiate root folder
    root_folder = MyFolder("root", parent="root", level=0, size=0)

    # iterate through all elements in root folder
    root_elements = ftp.nlst("")
    for i, element in enumerate(root_elements):

        # display scanning status to user
        progress_string = "\rScanning: {}".format(element)
        width = int(os.popen("stty size", "r").read().split()[1])  # get terminal width
        progress_string = progress_string.ljust(width)[: width - 2]  # adjust display
        print(progress_string, end="", flush=True)

        try: # subfolder case

            # if we can CD to this element, it's a subfolder
            ftp.cwd(element)

            # scan subfolder
            subfolder = scan_ftp_folder(
                ftp, os.path.join("/", element), parent=root_folder,
            )

            # cd back to current folder
            ftp.cwd("/")

            # add size of subfolder to this folder's tree_size
            root_folder.size += subfolder.size

            # add subfolder to this folder's children
            root_folder.children.append(subfolder)

        except: # file case

            # get file size
            ftp.voidcmd(
                "TYPE I"
            )  # avoid ftplib.error_perm: 550 SIZE not allowed in ASCII mode
            file_size = ftp.size(element)

            # add size of file to this folder's size
            root_folder.size += file_size

            # add new file to this folder's children
            root_folder.children.append(
                MyFile(element, parent=root_folder, size=file_size)
            )

    curses.wrapper(user_interface, root_folder)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-hst", "--host")
    parser.add_argument("-usr", "--user")
    parser.add_argument("-pwd", "--password")
    args = parser.parse_args()

    main(args.host, args.user, args.password)

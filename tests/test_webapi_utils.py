import os
import shutil

from ocrd_webapi.utils import (
    bagit_from_url
)

# Bigger mets file producing OCRD-ZIP that is bigger than 16MB (will be useful for DB tests)
# has only the "DEFAULT" file group
test_url = "https://content.staatsbibliothek-berlin.de/dc/PPN1027800947.mets.xml"
# Smaller mets file that has few file groups
test_url2 = "https://content.staatsbibliothek-berlin.de/dc/PPN1027800947.mets.xml"


# Fast and dirty tests - file existence checked, content not checked
def test_bagit_from_url_default_mets():
    test_dest_ext = "/tmp/webapi_utils_test1"
    dest = bagit_from_url(mets_url=test_url,
                          mets_basename="mets.xml",
                          dest=test_dest_ext,
                          file_grp="DEFAULT",
                          ocrd_identifier="test123")
    assert dest == f"{test_dest_ext}/test123.zip"
    assert os.path.exists(os.path.join(test_dest_ext, 'mets.xml'))
    assert os.path.exists(os.path.join(test_dest_ext, 'test123.zip'))
    shutil.rmtree(test_dest_ext)


def test_bagit_from_url_diff_mets():
    test_dest_ext = "/tmp/webapi_utils_test2"
    dest = bagit_from_url(mets_url=test_url2,
                          mets_basename="mets_diff.xml",
                          dest=test_dest_ext,
                          file_grp="DEFAULT",
                          ocrd_identifier="test456")
    assert dest == f"{test_dest_ext}/test456.zip"
    assert os.path.exists(os.path.join(test_dest_ext, 'mets_diff.xml'))
    assert os.path.exists(os.path.join(test_dest_ext, 'test456.zip'))
    shutil.rmtree(test_dest_ext)


def test_bagit_from_url_two_file_grps():
    test_dest_ext = "/tmp/webapi_utils_test3"
    dest = bagit_from_url(mets_url=test_url2,
                          mets_basename="mets.xml",
                          dest=test_dest_ext,
                          file_grp=["DEFAULT", "THUMBS"],
                          ocrd_identifier="test789")
    assert dest == f"{test_dest_ext}/test789.zip"
    assert os.path.exists(os.path.join(test_dest_ext, 'mets.xml'))
    assert os.path.exists(os.path.join(test_dest_ext, 'test789.zip'))
    shutil.rmtree(test_dest_ext)

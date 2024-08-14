import os
import time
import shutil
import datetime
import sys
import xml.etree.ElementTree as ET
import json
from mcrcon import MCRcon

os.system("cls")

print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Plugin-Tools by Bliffbot")
print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Version 1.0.0")
print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] ")

if os.path.exists(sys.argv[1]):
	with open(sys.argv[1], "r") as configFile:
		config = json.load(configFile)

	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Plugin Name: {config['pluginName']}")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Project Folder: {config['projectPath']}")
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] getting plugin version...")

	try:
		tree = ET.parse(f"{config['projectPath']}/pom.xml")
		try:
			root = tree.getroot()
			namespace = root.tag[root.tag.find('{')+1:root.tag.find('}')]
			version_element = root.find(f'{{{namespace}}}version')
			pluginVersion = version_element.text
			print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Plugin Version: {pluginVersion}")

			if config["setNextVersion"] == "true":
				try:
					version = pluginVersion.split(".")
					if len(version) == 5:
						version[4] = str(int(version[4]) + 1)
						newVersion = ".".join(version)
					elif len(version) == 3:
						version[2] = str(int(version[2]) + 1)
						newVersion = ".".join(version)

					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Next Version: {newVersion}")
					version_element.text = newVersion

					try:
						tree.write("pom.xml", xml_declaration=True, encoding='utf-8', method="xml",default_namespace=namespace)
						print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] set the next plugin version in the pom.xml")
					except:
						print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] could not update the plugin version in the pom.xml")
				except:
					newVersion = pluginVersion
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] weird version in pom.xml -> did not modify")
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] please use major.minor.patch.test.revision")
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] the parts need to be separated by dots")
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] e.g. 1.2.3 or 1.2.3.beta.4")
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] Next Version: {newVersion}")

			fileName = f"{config['pluginName']}-{pluginVersion}.jar"
			print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] File Name: {fileName}")
			jarPath = f"{config['projectPath']}/target/{fileName}"

			if os.path.exists(jarPath):
				print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] jar found")
				time.sleep(2)

				print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] cleaning the tidy folders...")
				folderNumber = 0
				while folderNumber < len(config['tidyFolders']):
					folder = str(config['tidyFolders'][folderNumber])
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {folderNumber + 1}/{len(config['tidyFolders'])} - {folder}")

					if not folder.endswith("/"):
						folder = folder + "/"

					try:
						for file in os.listdir(folder):
							if file.startswith(config['pluginName']) and os.path.isfile(folder + file):
								try:
									os.remove(folder + file)
									print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}]     {file} deleted")
								except Exception as error:
									print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}]     {file} not deleted - {error}")

					except:
						print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] could not clean up the tidy folders")

					folderNumber = folderNumber + 1
				print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] tidy folders cleaned")

				print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] coping to the copy folders...")
				folderNumber = 0
				while folderNumber < len(config["copyFolders"]):
					folder = str(config["copyFolders"][folderNumber])
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {folderNumber + 1}/{len(config['copyFolders'])} - {folder}")

					if not folder.endswith("/"):
						folder = folder + "/"

					try:
						shutil.copy(jarPath, folder)
						print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}]     copied")
					except Exception as error:
						print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}]     not copied - {error}")

					folderNumber = folderNumber + 1
				print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] copied to copy folders")

				if config["sendServerCommand"] == "true":
					print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] sending server commands...")
					with MCRcon(config["rconIP"], config["rconPassword"], port = int(config["rconPort"])) as mcr:
						for command in config["rconCommand"]:
							response = mcr.command(command)
							print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {command}")
							print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] {response}")

				print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] done :)")

			else:
				print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] jar not found")

		except:
			print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] could not find the version in {config['projectPath']}/pom.xml")
			print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] check if the file is properly formatted")
	except:
		print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] could not parse the content of {config['projectPath']}/pom.xml")
else:
	print(f"[{datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')}] could not find the config at {sys.argv[1]}")
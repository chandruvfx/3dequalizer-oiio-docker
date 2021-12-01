#
# 3DE4.script.name:	Convert 
#
# 3DE4.script.version:	v1.0
#
# 3DE4.script.gui:	Main Window::FWX Tools
#
# 3DE4.script.comment:	Add comment here.
#

# A master function node which converts user selected image sequence into jpg format
from time import process_time
from engine_config import TDE4BaseFactory
import subprocess
import threading
import sgtk
import os
import re

uname = os.getenv('USER')

destination_path = \
                os.path.join(
                '/Shares/T/SHOTGUNPRO/system_backup/3D_render/Artist_folder/plate_conversion/',
                uname )

scene_file = tde4.getProjectPath()

if scene_file is not None and scene_file.startswith('/Shares/T/studio/projects'):
    
    if '3de4' not in os.path.dirname(scene_file):
        scene_file_prj_folder_path =os.path.join(
                os.path.dirname(scene_file), '3de4')
    else:
        scene_file_prj_folder_path = os.path.dirname(scene_file)
        
    non_shot_config = TDE4BaseFactory(None)

    sgtk_shot_entity = non_shot_config.sgtk_resolve_path_from_context(scene_file)
    get_shot = sgtk_shot_entity.entity['name']

    shot_config = TDE4BaseFactory(str(get_shot))
    sg_shot_info = shot_config.sgtk_find_shot()


    def get_oiio_docker_status() -> bool:
        
        """[summary]
        Check status of the docker conatainer. If image exists it pull
        and create the container of oiio

        Returns:
            bool: Returns True if docker exists
        """

        
        tde4.postProgressRequesterAndContinue("Process...","Checking OpenImageIo Docker ..",1,"Ok")
        docker_container_call = subprocess.Popen('docker ps -a | grep 3de_oiio', \
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        docker_container_status, error = docker_container_call.communicate()
        tde4.updateProgressRequester(0,"Docker Status ...")
        
        if not docker_container_status:

            tde4.updateProgressRequester(3,"OIIO Docker Container Not exist ...") 
            docker_image_call = subprocess.Popen('docker images | grep localhost:5000/oiio/python3.6.12', \
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
            docker_image_status, error = docker_image_call.communicate()

            if not docker_image_status:

                tde4.postQuestionRequester(
                                            "FWX SGTK Info..",
                                            f"Docker Image for OIIO not Installed or Running! Please Contact IT",
                                            "Ok"
                                            )
                return False
            
            else:

                tde4.postProgressRequesterAndContinue("Process...","OIIO Docker Image Exsists. Installing ..",1,"Ok")
                os.system('docker run -dit --name 3de_oiio -v /Shares/T:/Shares/T localhost:5000/oiio/python3.6.12:v1 /bin/bash')
                tde4.updateProgressRequester(3,"OIIO Docker Container Created ...")

        else:
            
            tde4.updateProgressRequester(3,"Docker OIIO Exists ...")
            return True


    def make_folders(path: str):

            ''' Make Folders'''
            
            try:
                os.makedirs(path)
            except:
                pass
        

    def jpg_image_convert(publish_path: str, extension: str, lock: object) -> None:

        """[summary]
        COvert the user selcted input to jpg image . works for dpx and exr
        """

        
        os.system('docker start 3de_oiio')
        make_folders(destination_path)
        
        tty_file = '/tmp/3de_tty.txt'
        os.system(f'touch {tty_file}')
        os.system('konsole --hold -e sh -c \'tty > %s\'' %tty_file)
        
        tty_no = str
        with open(f'{tty_file}', 'r') as tty_file:
            tty_no = tty_file.read()    
   
        os.system(f'echo -e "\33[0;31mConverting Images\33[0;37m" > {tty_no}')
        dir_path = os.path.dirname(publish_path)
        for exr_files in os.listdir(dir_path):

                if exr_files.endswith(extension):
                    #extract name of files
                    destination_file_name = exr_files.split(extension)[0]
                    img_path = os.path.join(dir_path, exr_files)

                    with lock:
                        exec = f'docker exec 3de_oiio \
                                    /opt/oiio/build/bin/iconvert -v \
                                    {img_path} {destination_path}/{destination_file_name}.jpg > {tty_no}'
                        os.system(exec)

                    
                    
    def publish(extension: str, lock: object) ->  None:

        """
        Publish the Generated JPG to Shotgrid inthe Tracking task
        """
        
        get_single_image = os.listdir(destination_path)[0]
        get_version = re.search('v\d{3}', get_single_image).group(0)
        
        # Extract Frame number with underscore or dot from the seq image Ex _100002
        # From pub_dev7_Tracking_v001_100002.jpg
        frame_no_ext = str(get_single_image.split(get_version)[-1].split('.jpg')[0])
        filter_no = ''.join(filter( lambda num: num.isdigit(), frame_no_ext ))
        length = len(filter_no)


        current_tde_pub_scene_path = shot_config.sgtk_resolve_publish_path_jpg()
        versions =[]
        version = 0
        
        jpg_file_name = os.path.basename(current_tde_pub_scene_path)
        partial_jpg_file_name = jpg_file_name.replace('%04', '%0{}'.format(length))

        # Some times the publishing input file name version is differ from 
        # published version. so we extraaacting input publish file for 
        # extracting version number. 
        # Example 
        #
        # if publishing file is pub_dev7_Tracking_v002_%04d.jpg  
        # and published file is pub_dev7_Tracking_v001_%06d.jpg then 
        # 'get_version' is v001 and 'get_current_file_version' is v002
        # so we check if maches or not and exttracting pub_dev7_Tracking_
        get_current_file_version  = re.search('v\d{3}', partial_jpg_file_name).group(0)
        
        if get_current_file_version == get_version:
            search_jpg_file = partial_jpg_file_name.split(get_version)[0]
        else:
            search_jpg_file = partial_jpg_file_name.split(get_current_file_version)[0]

        with lock:
            get_pub_dict = shot_config.sgtk_find_published_files()
            
            if get_pub_dict != {}:
                for published_jpg_files,_ in get_pub_dict.items():
                    if search_jpg_file in published_jpg_files and \
                                published_jpg_files.endswith('.jpg') or \
                                published_jpg_files.endswith('.jpeg') or \
                                published_jpg_files.endswith('.JPG') or \
                                published_jpg_files.endswith('.JPEG'):


                        # Some times when we gathering publish files outputes are
                        # pub_dev7_Tracking_v001, pub_dev7_Tracking_v002, pub_dev7_Tracking_MMtrack_v003
                        # Nowif or publish conversion is pub_dev7_Tracking_ then new verison will be 4
                        # because it take it account all .jpg ending file. 
                        # So we get last charecter what e publishing EX: if pub_dev7_Tracking_ is out publish
                        # this below one extract '_' and check 'v001' string after the publish string
                        # If it is there then it only take that version number has latest
                        #  Example:
                        #
                        # If we try publish pub_dev7_Tracking_ and exsisting files are
                        # pub_dev7_Tracking_v001, pub_dev7_Tracking_v002, pub_dev7_Tracking_MMtrack_v003 Means
                        # pub_dev7_Tracking_MMtrack_v003 for omitted
                        get_last_char_index = int(search_jpg_file.rfind(search_jpg_file[-1]))
                        get_version_info = published_jpg_files[get_last_char_index+1:]
                        
                        if re.search('^v\d{3}', get_version_info) is not None:

                            # Extract 'v001
                            pub_version_str= re.search('v\d{3}', published_jpg_files).group(0)
                            # Extract 001 from v. and make it integer
                            pub_version_no = int(re.search('\d{3}', pub_version_str).group(0))
                            versions.append(pub_version_no)
                            
                            
                max_ver = max(versions) if versions else 0
                version = max_ver + 1
            
                # Resolve the publish path with the new version
                version_up_current_jpg_pub_path = shot_config.sgtk_resolve_publish_path_jpg(version)
                
                # Get file name and create the name for inbetween dir
                jpg_extracted_file_name = os.path.basename(version_up_current_jpg_pub_path)
                jpg_extracted_dir_path = os.path.dirname(version_up_current_jpg_pub_path)
                
                extract_version = re.search('v\d{3}', jpg_extracted_file_name).group(0)
                partial_jpg_file_name = jpg_extracted_file_name.split(extract_version)[0]

                # If file name is pub_dev7_Tracking_v002_%06d.jpg then it provide pub_dev7_Tracking_v002
                #dir_name = partial_jpg_file_name + extract_version
                make_folders(jpg_extracted_dir_path)
                
                # Change %04d in image seq to the original extracted one
                padding_changed_path = jpg_extracted_file_name.replace('%04', '%0{}'.format(length))
                final_publish_image = os.path.join(
                            jpg_extracted_dir_path,
                            padding_changed_path)


                # Create Instace of sgtk for future use
                tk = sgtk.sgtk_from_path(shot_config.get_project_path())
                tk.synchronize_filesystem_structure()
                
                ctx = tk.context_from_path(version_up_current_jpg_pub_path)
                
                f = [[ 'entity', 'is', {'type': 'Shot', 'id': sg_shot_info[0]['id']} ]]

                # Get tthe tracking task id to use in publish register
                track_task = dict
                task_schema = tk.shotgun.find('Task', f, ['content'])

                for task in task_schema:
                    
                    if task['content'] == 'Tracking':
                        
                        track_task = task
                        
                if track_task == '':
                    tde4.postQuestionRequester(
                            "FWX SGTK Warning..",
                            f"Tracking Task Not exist in SG!!",
                            "Ok"
                            )
                        
                else:

                    sgtk.util.register_publish(tk=tk,
                                            context=ctx,
                                            path=final_publish_image,
                                            task=track_task,
                                            name= jpg_extracted_file_name,
                                            version_number = version,
                                            published_file_type = 'Rendered Image'
                                            )
                    
                    final_publish_dirpath = os.path.dirname(
                                    final_publish_image
                                    )
                    make_folders(final_publish_dirpath)
                    tty_file = '/tmp/3de_tty.txt'
                    #os.system(f'touch {tty_file}')
                    #os.system('konsole --hold -e sh -c \'tty > %s\'' %tty_file_cp)

                    tty_no_cp = str
                    with open(f'{tty_file}', 'r') as tty_file1:
                        tty_no_cp = tty_file1.read()    

                    os.system(f'echo -e "\33[0;31mCopying Publish Images\e[37m" > {tty_no_cp}')
                    for publish_imgs in os.listdir(destination_path):

                        partial_new_file_name = jpg_extracted_file_name.split('%')[0]
                        get_version = re.search('v\d{3}', publish_imgs).group(0)

                        # Extract Frame number with underscore or dot from the seq image Ex 100002
                        # From pub_dev7_Tracking_v001_100002.jpg
                        frame_no_ext = str(publish_imgs.split(get_version)[-1].split('.jpg')[0])
                        frame_no = ''.join(filter( lambda num: num.isdigit(), frame_no_ext ))
                                    
                        jpc_file_name = partial_new_file_name + frame_no + '.jpg'
                        source_full_path = os.path.join(
                                    destination_path,
                                    publish_imgs )
                        pub_destination_path = os.path.join(
                                        final_publish_dirpath,
                                        jpc_file_name 
                                    )
                        
                        os.system(f'cp -vrf {source_full_path} {pub_destination_path} > {tty_no_cp}')

    def cleanup(lock) -> None:

            with lock:
                for img_files in os.listdir(destination_path):
                    src_image_files = os.path.join(
                                destination_path, img_files
                        )
                    
                    os.system(f'rm -rvf {src_image_files}')
                    
                    
        
    def convert(requester,widget,action):

        if widget == "convert_publish":

            try:

                index = tde4.getListWidgetSelectedItems(requester, "img_plate_list")[0]
                selected_element_file = tde4.getListWidgetItemLabel(requester, "img_plate_list",index)
                resolved_publish_dict = shot_config.sgtk_find_published_files()

                extensions = ['.exr', '.dpx']
                for extension in extensions:
                    for publish_name, publish_path in resolved_publish_dict.items():
                        if selected_element_file == publish_name:
                            if publish_path.endswith(extension):
                            
                                #intiate thread for img convert. accuire lock for
                                # each operation . so always one start after one finish
                                lock = threading.Lock()
                                img_thread = threading.Thread(
                                            target=jpg_image_convert, 
                                            args=(publish_path, extension, lock)
                                            )
                                img_thread.start()
                                img_thread.join()

                                publish_thread = threading.Thread(
                                            target=publish,
                                            args=(extension, lock)
                                            )
                                publish_thread.start()
                                publish_thread.join()

                                cleanup_thread = threading.Thread(
                                            target=cleanup,
                                            args=(lock, )
                                            )
                                cleanup_thread.start()
                                cleanup_thread.join()
                        

            except: pass
            
        return


    def _ConvertUpdate(requester):

        if get_oiio_docker_status():
            
            tde4.removeAllListWidgetItems(requester,"img_plate_list")
            resolved_publish_dict = shot_config.sgtk_find_published_files()
            
            exr_index = tde4.insertListWidgetItem(requester, "img_plate_list",'Exr\'s',0,"LIST_ITEM_NODE")
            for publish_name, _ in resolved_publish_dict.items():
                if publish_name.endswith('.exr'):
                    tde4.insertListWidgetItem( requester, "img_plate_list",
                                            publish_name, exr_index,
                                            "LIST_ITEM_ATOM", exr_index )
                    
            dpx_index = tde4.insertListWidgetItem(requester, "img_plate_list",'Dpx\'s',1,"LIST_ITEM_NODE")  
            for publish_name, _ in resolved_publish_dict.items():
                if publish_name.endswith('.dpx'):
                    tde4.insertListWidgetItem( requester, "img_plate_list",
                                            publish_name, dpx_index,
                                            "LIST_ITEM_ATOM", dpx_index )
                    
        
        return


    #
    # DO NOT ADD ANY CUSTOM CODE BEYOND THIS POINT!
    #

    try:
        requester	= _Convert_requester
    except (ValueError,NameError,TypeError):
        requester = tde4.createCustomRequester()
        tde4.addListWidget(requester,"img_plate_list","Image Plate List",0)
        tde4.setWidgetOffsets(requester,"img_plate_list",124,0,36,0)
        tde4.setWidgetAttachModes(requester,"img_plate_list","ATTACH_WINDOW","ATTACH_NONE","ATTACH_WINDOW","ATTACH_NONE")
        tde4.setWidgetSize(requester,"img_plate_list",600,450)
        tde4.setWidgetCallbackFunction(requester,"img_plate_list","convert")
        tde4.addButtonWidget(requester,"convert_publish","Convert & Publish")
        tde4.setWidgetOffsets(requester,"convert_publish",353,0,506,0)
        tde4.setWidgetAttachModes(requester,"convert_publish","ATTACH_WINDOW","ATTACH_NONE","ATTACH_WINDOW","ATTACH_NONE")
        tde4.setWidgetSize(requester,"convert_publish",150,30)
        tde4.setWidgetCallbackFunction(requester,"convert_publish","convert")
        tde4.setWidgetLinks(requester,"img_plate_list","","","","")
        tde4.setWidgetLinks(requester,"convert_publish","","","","")
        _Convert_requester = requester

    #
    # DO NOT ADD ANY CUSTOM CODE UP TO THIS POINT!
    #

    if tde4.isCustomRequesterPosted(_Convert_requester)=="REQUESTER_UNPOSTED":
        if tde4.getCurrentScriptCallHint()=="CALL_GUI_CONFIG_MENU":
            tde4.postCustomRequesterAndContinue(_Convert_requester,"Convert ",0,0,"_ConvertUpdate")
        else:
            tde4.postCustomRequesterAndContinue(_Convert_requester,"Convert  v1.0",800,600,"_ConvertUpdate")
    else:	tde4.postQuestionRequester("_Convert","Window/Pane is already posted, close manually first!","Ok")

else:

    tde4.postQuestionRequester(
                "FWX SGTK Info..",
                f"SGTK Environment is Not Initialized\n\
                Please set using MainWindow's Shotgrid -> Set Env",
                "Ok"
                )
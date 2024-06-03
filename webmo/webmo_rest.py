import requests
import json
import asyncio
import numpy as np

try:
    from IPython.display import display, clear_output, Javascript, Image
    has_ipython = True
except ImportError:
    has_ipython = False

class WebMOREST:
    """The WebMOREST class provides an object-oriented Python API for the WebMO REST interface.
    
    The WebMOREST class provides a simple Python API to access the WebMO REST interface. As of now
    there are no public methods. Session tokens are handled automatically handled during object
    creation/destruction.
    """
    
    def __init__(self, base_url, username, password=""):
        """Constructor for WebMOREST
        
        This constructor generates a WebMOREST object and also generates and stores a newly
        session token.
        
        Args:
            base_url(str): The base URL (ending in rest.cgi) of the WeBMO rest endpoint
            username(str): The WebMO username
            password(str, optional): The WebMO password; if omitted, this is supplied interactively
            
        Returns:
            object: The newly constructed WebMO object
        """
        from getpass import getpass
        
        #prompt for WebMO password if not specified
        if not password:
            password=getpass(prompt="Enter WebMO password for user %s:" % username)
        #obtain a REST token using the specified credentials
        login={'username' : username, 'password' : password} #WebMO login information, used to retrieve a REST access token
        r = requests.post(base_url + '/sessions', data=login)
        r.raise_for_status() #raise an exception if there is a problem with the request
        
        self._base_url = base_url
        self._auth=r.json() #save an authorization token need to authenticate future REST requests
        
        if has_ipython:
            self._init_javascript = True
            self._callback_listener = None
        
    def __del__(self):
        """Destructor for WebMOREST
        
        This destructor automatically deletes the session token using the REST interface
        """
        #End the REST sessions
        r = requests.delete(self._base_url + '/sessions', params=self._auth)
        #do not raise an exception for a failed request in this case due to issues
        #with object management in Jupyter (i.e. on code re-run, a new token is made
        #prior to deletion!)

        if self._callback_listener is not None:
            self._callback_listener.close()
    
    #
    # Users resource
    # 
    def get_users(self):
        """Fetches a list of available WebMO users
        
        This call returns a list of available WebMO users. For non-administrative users, this will be
        only the current authenticated user. For group administrators, this call will return all users
        in the group. For system administrators, this call will return all system users.
        
        Returns:
            A list of users
        """
        
        r = requests.get(self._base_url + "/users", params=self._auth)
        r.raise_for_status()
        return r.json()["users"]
        
    def get_user_info(self, username):
        """Returns information about the specified user
        
        This call returns a JSON formatted string summarizing information about the requested user. For non-
        administrative users, only requests for the authenticated user will be accepted.
        
        Arguments:
            username(str): The username about whom to return information
            
        Returns:
            A JSON formatted string summarizing the user information
        """
        
        r = requests.get(self._base_url + "/users/%s" % username, params=self._auth)
        r.raise_for_status()
        return r.json()

    #
    # Groups resource
    # 
    def get_groups(self):
        """Fetches a list of available WebMO groups
        
        This call returns a list of available WebMO groups. For non-administrative users, this will be
        only the current authenticated group. For system administrators, this call will return all system groups.
        
        Returns:
            A list of groups
        """
        
        r = requests.get(self._base_url + "/groups", params=self._auth)
        r.raise_for_status()
        return r.json()["groups"]
        
    def get_group_info(self, groupname):
        """Returns information about the specified group
        
        This call returns a JSON formatted string summarizing information about the requested group. For non-
        administrative users, only requests for the authenticated group will be accepted.
        
        Arguments:
            groupname(str): The groupname about whom to return information
            
        Returns:
            A JSON formatted string summarizing the group information
        """
        
        r = requests.get(self._base_url + "/groups/%s" % groupname, params=self._auth)
        r.raise_for_status()
        return r.json()
        
        
    #
    # Folders resource
    # 
    def get_folders(self, target_user=""):
        """Fetches a list of folders owned by the current user or the specified target user
        
        This call returns a list of available folders. Administrative users must specify the target user,
        otherwise the folders owned by the current user are returned.
        
        Arguments:
            target_user(str, optional): The target username whose folders are retrieved. Otherwise, uses the authenticated user.
        
        Returns:
            A list of folders
        """
        
        #append other relevant paramters
        params = self._auth.copy()
        params.update({'user' : target_user})
        r = requests.get(self._base_url + "/folders", params=params)
        r.raise_for_status()
        return r.json()["folders"]
    
    #
    # Jobs resource
    #
    def get_jobs(self, engine="", status="", folder_id="", job_name="", target_user=""):
        """Fetches a list of jobs satisfying the specified filter criteria
        
        This call returns a list of available jobs owned by the current user or (for administrative users)
        the specified target user AND the specified filter criteria.
        
        Arguements:
            engine(str, optional): Filter by specified computational engine
            status(str, optional): Filter by job status
            folder_id(str, optional): Filter by folder ID (not name!)
            target_user(str, optional): The target username whose jobs are retrieved. Otherwise, uses the authenticated user.
        
        Returns:
            A list of jobs meeting the specified criteria
        """
                
        #append other relevant paramters
        params = self._auth.copy()
        params.update({'engine' : engine, 'status' : status, 'folderID' : folder_id, 'jobName' : job_name, 'user' : target_user})
        r = requests.get(self._base_url + '/jobs', params=params)
        r.raise_for_status()
        return r.json()["jobs"]
        
    def get_job_info(self, job_number):
        """Returns information about the specified job
        
        This call returns a JSON formatted string summarizing basic information about the requested job.
        
        Arguments:
            job_number(int): The job about whom to return information
            
        Returns:
            A JSON formatted string summarizing the job information
        """
        
        r = requests.get(self._base_url + "/jobs/%d" % job_number, params=self._auth)
        r.raise_for_status()
        return r.json()
        
    def get_job_results(self, job_number):
        """Returns detailed results of the calculation (e.g. energy, properties) from the specified job.
        
        This call returns a JSON formatted string summarize all of the calculated and parsed properties
        from the specified job. This information is normally summarized on the View Job page.
        
        Arguments:
            job_number(int): The job about whom to return information
            
        Returns:
            A JSON formatted string summarizing the calculated properties
        """
        
        r = requests.get(self._base_url + "/jobs/%d/results" % job_number, params=self._auth)
        r.raise_for_status()
        return r.json()
        
    def get_job_geometry(self, job_number):
        """Returns the final optimized geometry from the specified job.
        
        This call returns an XYZ formatted file of the final optimized geometry from the specified job.
        
        Arguments:
            job_number(int): The job about whom to return information
            
        Returns:
            A string containing XYZ formatted optimized geometry
        """
        
        r = requests.get(self._base_url + "/jobs/%d/geometry" % job_number, params=self._auth)
        r.raise_for_status()
        return r.json()["xyz"]
        
    def get_job_output(self, job_number):
        """Returns the raw text output from the specified job.
        
        This call returns the textual raw output file from the specified job.
        
        Arguments:
            job_number(int): The job about whom to return information
            
        Returns:
            A string containing the contents of the raw output file
        """
        
        r = requests.get(self._base_url + "/jobs/%d/raw_output" % job_number, params=self._auth)
        r.raise_for_status()
        return r.text
        
    def get_job_archive(self, job_number):
        """Returns a WebMO archive from the specified job.
        
        This call generates and returns a binary WebMO archive (tar/zip) file from the specified job.
        
        Arguments:
            job_number(int): The job about whom to generate the archive
            
        Returns:
            The raw data (as a string) of the WebMO archive, appropriate for saving to disk
        """
        
        r = requests.get(self._base_url + "/jobs/%d/archive" % job_number, params=self._auth)
        r.raise_for_status()
        return r.text
        
    def delete_job(self, job_number):
        """Permanently deletes a WebMO job 
        
        This call deletes the specified job.
        
        Arguments:
            job_number(int): The job to delete
        """
        
        r = requests.delete(self._base_url + "/jobs/%d" % job_number, params=self._auth)
        r.raise_for_status()
        
    def import_job(self, job_name, filename, engine):
        """Imports an existing output file into WebMO
        
        This call imports an existing computational output file, parsing the output and creating a newly
        WebMO job.
        
        Arguments:
            job_name(str): The name of the new WebMO job
            filename(str): The filename (full path) of an existing output file to import
            engine(str): The name of the computational engine
            
        Returns:
            The the job number of the new job, upon success
        """
        
        params = self._auth.copy()
        params.update({'jobName' : job_name, 'engine' : engine})
        output_file = {'outputFile' : ('output.log', open(filename, 'rb'), 'text/plain')}
        r = requests.post(self._base_url + '/jobs', data=params, files=output_file)
        r.raise_for_status()
        return r.json()["jobNumber"]
        
    def submit_job(self, job_name, input_file_contents, engine, queue=None):
        """Submits and executes a new WebMO job
        
        This call submits and executes a new job to a computational engine, generating a new WebMO job.
        
        Arguments:
            job_name(str): The name of the new WebMO job
            input_file_contents(str): The contents of a valid input file to submit to a computational engine
            engine(str): The name of the computational engine
            
        Returns:
            The the job number of the new job, upon success
        """
        
        params = self._auth.copy()
        params.update({'jobName' : job_name, 'engine' : engine, 'inputFile': input_file_contents, 'queue': queue})
        r = requests.post(self._base_url + '/jobs', data=params)
        r.raise_for_status()
        return r.json()["jobNumber"]
        
    async def display_job_property(self, job_number, property_name, property_index=1, peak_width=0.0, tms_shift=0.0, proton_coupling=0.0, nmr_field=400.0, x_range=None, y_range=None, width=400, height=400, background_color=(255,255,255), transparent_background=False, rotate=(0.,0.,0.)):
        """Uses Javascript and IPython to display an image of the specified molecule and property,
        calculated from a previous WebMO job.
        
        This call outputs (via IPython) a PNG-formatted image of the molecule and property into the
        Jupyter notebook cell. Requires IPython and WebMO 24 or higher. This is an asynchronous
        method that must be 'await'ed, e.g. image = await rest.display_job_property(...)
        
        Arguments:
            job_number(int): The job about whom to return information
            property_name(str): The name of the property to display. Must be one of 'geometry', 'dipole_moment', 'partial_charges', 'vibrational_mode', 'mo' (molecular orbital), 'esp' (electrostatic potential), 'nucleophilic', 'electrophilic', 'radical', 'nbo' (natural bonding orbital), 'nho' (natural hybrid orbital), 'nao' (natural atomic orbital), or various spectra ('ir_spectrum', 'raman_spectrum', 'vcd_spectrum', 'uvvis_spectrum', 'hnmr_spectrum', 'cnmr_spectrum')
            property_index(int, optional): The 1-based index of the property to display, e.g. which vibrational or orbital

            x_range(float,float,optional): A tuple specifying the min/max x-range for spectra; can be reversed to invert axis
            y_range(float,float,optional): A tuple specifying the min/max y-range for spectra; can be reversed to invert axis
            peak_width(float, optional): The peak width to use for spectra; default is spectrum-type specific
            tms_shift(float, optional): The chemical shift of TMS (in ppm, at same level of theory), which can be used for H1 NMR spectra
            proton_coupling(float, optional): The proton-proton coupling (in Hz), which can be used for H1 NMR spectra
            nmr_field(float, optional): The NMR field strength (in MHz), which can be used for H1 NMR spectra

            width(int, optional): The approximate width (in pixels) of the image to display (defaults to 400px)
            height(int, optional): The approximate height (in pixels) of the image to display (defaults to 300px)
            background_color(int,int,int,optional): A tuple specifying the (r,g,b) color of the background, where each color intensity is [0,255]
            transparent_background(boolean,optional): Whether the background is transparent or opaque
            rotate(int,int,int,optional): A tuple specifying the desired rotation (in degrees) of the molecule about the x,y,z axes about the "default" orientation
            
        Returns:
            An EmbeddedImage object, which can be displayed and further manipulated.
        """
        from math import sqrt

        self._check_ipython()

        if self._init_javascript:
            print("Loading required Javascript...")
            self._inject_javascript()

        if self._callback_listener is None:
            await self._create_callback_listener()

        r = requests.get(self._base_url + "/jobs/%d/geometry" % job_number, params=self._auth)
        r.raise_for_status()
        geometryJSON = json.dumps(r.json())
        geometryJSON = geometryJSON.replace("\\", "\\\\")
        
        results = self.get_job_results(job_number)
        
        javascript_string = self._set_moledit_size(width,height)
        javascript_string += self._set_moledit_background(background_color[0],background_color[1],background_color[2])
        javascript_string += self._set_moledit_geometry(geometryJSON)
        
        if property_index <= 0:
            raise ValueError("Invalid property_index specified")
        
        property_string = ""
        WAVEFUNCTION_PROPERTIES = ["mo", "nao", "nho", "nbo", "esp", "nucleophilic", "electrophilic", "radical"]
        SURFACE_PROPERTIES = ["esp", "nucleophilic", "electrophilic", "radical"]
        if property_name == "geometry":
            #do nothing special
            pass

        elif property_name == "dipole_moment":
            dipole_moment = results['properties']['dipole_moment']
            total_dipole = sqrt(dipole_moment[0]**2 + dipole_moment[1]**2 + dipole_moment[2]**2)
            property_string = "%f:%f:%f:%f" % (*dipole_moment,total_dipole)
            javascript_string += self._set_moledit_dipole_moment(property_string)
            
        elif property_name == "partial_charges":
            partial_charges = results['properties']['partial_charges']['mulliken']
            for i in range(len(partial_charges)):
                property_string += "%d,X,%f:" % (i+1,partial_charges[i])
            property_string = property_string.rstrip(":")
            javascript_string += self._set_moledit_partial_charge(property_string)
            
        elif property_name == "vibrational_mode":
            frequency = results['properties']['vibrations']['frequencies'][property_index-1]
            displacements = results['properties']['vibrations']['displacement'][property_index-1]
            for i in range(len(displacements)//3):
                property_string += "%d,%f,%f,%f:" % (i+1,displacements[i*3+0],displacements[i*3+1],displacements[i*3+2])
            property_string = property_string.rstrip(":")
            javascript_string += self._set_moledit_vibrational_mode(property_string, property_index, frequency, 1.0)
            
        elif property_name in WAVEFUNCTION_PROPERTIES:
            if property_name in SURFACE_PROPERTIES:
                property_index = 0 #this is required
            javascript_string += self._rotate_moledit_view(rotate[0],rotate[1],rotate[2])
            javascript_string += self._set_moledit_wavefunction(job_number, property_name, property_index, transparent_background) #handles screenshot in callback
            
        elif property_name in ["ir_spectrum", "raman_spectrum", "vcd_spectrum"]:
            frequencies = results['properties']['vibrations']['frequencies']
            if property_name == "ir_spectrum":
                intensities = results['properties']['vibrations']['intensities']['IR']
            elif property_name == "raman_spectrum":
                intensities = results['properties']['vibrations']['intensities']['raman']
            else:
                intensities = results['properties']['vibrations']['intensities']['VCD']

            for i in range(len(frequencies)):
                property_string += "%d,-,%f,%f:" % (i+1,frequencies[i],intensities[i])
            property_string = property_string.rstrip(":")

            if property_name == "ir_spectrum":
                javascript_string += self._set_datagrapher_ir_spectrum(property_string, peak_width if peak_width > 0 else 40.0)
            elif property_name == "raman_spectrum":
                javascript_string += self._set_datagrapher_raman_spectrum(property_string, peak_width if peak_width > 0 else 40.0)
            else:
                javascript_string += self._set_datagrapher_vcd_spectrum(property_string, peak_width if peak_width > 0 else 40.0)

        elif property_name == "uvvis_spectrum":
            transition_energies = results['properties']['excited_states']['transition_energies']
            intensities = results['properties']['excited_states']['intensities']
            units = results['properties']['excited_states']['units']

            for i in range(len(transition_energies)):
                property_string += "%d,-,%f,%f:" % (i+1,transition_energies[i],intensities[i])
            property_string = property_string.rstrip(":")

            javascript_string += self._set_datagrapher_uvvis_spectrum(property_string, units, peak_width if peak_width > 0 else 20.0)

        elif property_name == "hnmr_spectrum" or property_name == "cnmr_spectrum":
            symbols = results['symbols']
            isotropic = results['properties']['nmr_shifts']['isotropic']
            anisotropy = results['properties']['nmr_shifts']['anisotropy']

            for i in range(len(isotropic)):
                if tms_shift > 0 and symbols[i] == "H":
                    isotropic[i] = tms_shift - isotropic[i] #apply the TMS shift, if provided
                property_string += "%d,%s,%f,%f:" % (i+1,symbols[i],isotropic[i],anisotropy[i])
            property_string = property_string.rstrip(":")

            atom_type = "C" if property_name == "cnmr_spectrum" else "H"
            peak_width  = peak_width if peak_width > 0 else 0.001
            relative_spectrum = 1 if tms_shift > 0 and atom_type == "H" else 0

            if atom_type == "H" and proton_coupling > 0:
                javascript_string += self._set_datagrapher_h1nmr_spectrum(property_string, peak_width, proton_coupling, nmr_field, relative_spectrum)
            else:
                javascript_string += self._set_datagrapher_nmr_spectrum(property_string, atom_type, peak_width, relative_spectrum)

        else:
            raise ValueError("Invalid property_name specified")
        
        if not property_name in WAVEFUNCTION_PROPERTIES: #these are already done in the setWavefunction callback
            if property_name.endswith("spectrum"):
                if x_range is not None:
                    javascript_string += self._set_x_range(x_range[0], x_range[1])
                if y_range is not None:
                    javascript_string += self._set_y_range(y_range[0], y_range[1])
                javascript_string += self._display_datagrapher_screenshot()
            else:
                javascript_string += self._rotate_moledit_view(rotate[0],rotate[1],rotate[2])
                javascript_string += self._display_moledit_screenshot(transparent_background)

        #display the Javascript for execution
        display(Javascript("_call_when_ready(function(){%s})" % javascript_string))
        clear_output()
        #wait for the Javascript callback and process / display the result
        return await self._process_callback_response()


    #
    # Status resource
    #
    def get_status_info(self):
        """Returns information about the specified WebMO instance
        
        This call returns a JSON formatted string summarizing basic status information about the specified WebMO instance.
        
        Arguments:
            None
            
        Returns:
            A JSON formatted string summarizing the status information
        """
        
        r = requests.get(self._base_url + "/status", params=self._auth)
        r.raise_for_status()
        return r.json()
        
        
    #
    # Helper functions
    #
    def wait_for_job(self, job_number, poll_frequency=5):
        """Waits for completion of the specified WebMO job
        
        This call blocks until the specified WebMO job has finished executing (successfully or not)
        
        Arguments:
            job_number(int): The job number to wait for
            poll_frequency(int, optional): The frequency at which to check the job status (default is 5s)
        """
        
        self.wait_for_jobs([job_number], poll_frequency)
    
    def wait_for_jobs(self, job_numbers, poll_frequency=5):
        """Waits for completion of the specified list of WebMO jobs
        
        This call blocks until the specified WebMO jobs have all finished executing (successfully or not)
        
        Arguments:
            job_numbers(list): A list of job numbers which will be waited upon
            poll_frequency(int, optional): The frequency at which to check the job status (default is 5s)
        """
        from time import sleep
        
        status = {}
        done = False
        
        for job_number in job_numbers:
            status[job_number] = ''

        while not done:
            done = True
            for job_number in job_numbers:
                if status[job_number] != 'complete' and status[job_number] != 'failed':
                    status[job_number] = self.get_job_info(job_number)['properties']['jobStatus']
                    if status[job_number] != 'complete' and status[job_number] != 'failed':
                        done = False
            if not done:
                sleep(poll_frequency)
            
    #
    # Private helper methods
    #
    
    def _inject_javascript(self):
        if self._init_javascript:
            config = self.get_status_info()
            major_version = int(config["version"].split(".")[0])
            
            #ensure WebMO support as well, otherwise disable IPython features
            if major_version < 24:
                global has_ipython
                has_ipython = False
                return
                
            try:
                ipython = get_ipython()
                ipython.run_cell_magic("html", "", "\
                <script src='%s/javascript/jquery.js'></script>\
                <script src='%s/javascript/moledit_js/moledit_js.nocache.js'></script>\
                <script src='%s/javascript/jupyter_moledit.js'></script>\
                <script>\
                    if(document.getElementById('moledit-panel'))\
                        document.getElementById('moledit-panel').remove();\
                    if(document.getElementById('datagrapher-panel'))\
                        document.getElementById('datagrapher-panel').remove();\
                    moledit_div = document.createElement('div');\
                    moledit_div.innerHTML = \"<DIV ID='moledit-panel' CLASS='gwt-app' STYLE='width:300px; height:300px; visibility: hidden; position: absolute' orbitalSrc='%s/get_orbital.cgi' viewOnly='true' isJupyter='true'></DIV><DIV ID='datagrapher-panel' CLASS='gwt-app' STYLE='width: 300px; height: 300px; visibility: hidden; position: absolute'></DIV>\";\
                    document.body.prepend(moledit_div);\
                    var exception_count = 0;\
                    function _call_when_ready(func) {\
                        const ready = document.getElementById('moledit-panel').children.length > 0 && document.getElementById('datagrapher-panel').children.length > 0 && _render_lock();\
                        if (!ready) {\
                            setTimeout(function() {_call_when_ready(func)}, 100);\
                            return;\
                        }\
                        try {\
                            func();\
                            exception_count=0;\
                        }\
                        catch(e) {\
                            console.log(e);\
                            _clear_lock();\
                            if (exception_count++ < 3)\
                                setTimeout(function() {_call_when_ready(func)}, 1000);\
                        }\
                    }\
                    function _render_lock() {\
                        if (window.render_lock > 0 && Date.now() - window.render_lock < 5000) {\
                            return false;\
                        }\
                        else {\
                            window.render_lock = Date.now();\
                            return true;\
                        }\
                    }\
                    function _clear_lock() {\
                        window.render_lock = 0;\
                    }\
                </script>" % (config['url_html'], config['url_html'], config['url_html'], config['url_cgi']))
                self._init_javascript = False
            except:
                has_ipython = False

    def _check_ipython(self):
        if not has_ipython:
            raise NotImplementedError("IPython and WebMO 24+ are required for this feature")
        
    def _set_moledit_geometry(self,geometryJSON):
        return "_set_moledit_geometry('%s');" % geometryJSON
        
    def _set_moledit_dipole_moment(self, value):
        return "_set_moledit_dipole_moment('%s');" % value
        
    def _set_moledit_partial_charge(self, value):
        return "_set_moledit_partial_charge('%s');" % value
        
    def _set_moledit_vibrational_mode(self, value, mode, freq, scale):
        return "_set_moledit_vibrational_mode('%s', %d, %f, %f);" % (value, mode, freq, scale)
    
    def _set_moledit_wavefunction(self, job_number, wavefunction_type, mo_index, transparent_background):
        return "_set_moledit_wavefunction(%d,'%s', %d, %d, %s);" % (job_number, wavefunction_type, mo_index, self._callback_port, 'true' if transparent_background else 'false')
        
    def _set_datagrapher_ir_spectrum(self, value, peak_width):
        return "_set_datagrapher_ir_spectrum('%s', %f);" % (value, peak_width)

    def _set_datagrapher_raman_spectrum(self, value, peak_width):
        return "_set_datagrapher_raman_spectrum('%s', %f);" % (value, peak_width)

    def _set_datagrapher_vcd_spectrum(self, value, peak_width):
        return "_set_datagrapher_vcd_spectrum('%s', %f);" % (value, peak_width)

    def _set_datagrapher_uvvis_spectrum(self, value, units, peak_width):
        return "_set_datagrapher_uvvis_spectrum('%s', '%s', %f);" % (value, units, peak_width)

    def _set_datagrapher_nmr_spectrum(self, value, atom_type, peak_width, relative_spectrum):
        return "_set_datagrapher_nmr_spectrum('%s', '%s', %f, %d);" % (value, atom_type, peak_width, relative_spectrum)

    def _set_datagrapher_h1nmr_spectrum(self, value, peak_width, proton_coupling, nmr_field, relative_spectrum):
        return "_set_datagrapher_h1nmr_spectrum('%s', %f, %f, %f, %d);" % (value, peak_width, proton_coupling, nmr_field, relative_spectrum)

    def _set_x_range(self, min, max):
        return "_set_x_range(%f, %f);" % (min, max)

    def _set_y_range(self, min, max):
        return "_set_y_range(%f, %f);" % (min, max)

    def _set_moledit_size(self,width,height):
        return "_set_moledit_size(%d,%d);" % (width, height)
        
    def _set_moledit_background(self,r,g,b):
        return "_set_moledit_background(%d,%d,%d);" % (r, g, b)
        
    def _rotate_moledit_view(self,rx,ry,rz):
         return "_rotate_moledit_view(%f,%f,%f);" % (rx, ry, rz)
            
    def _display_moledit_screenshot(self, transparent_background):
        return "_display_moledit_screenshot(%d,%s);" % (self._callback_port, 'true' if transparent_background else 'false')

    def _display_datagrapher_screenshot(self):
        return "_display_datagrapher_screenshot(%d);" % self._callback_port

    #
    # Methods for handling WebSocket data connections and callbacks
    #
    async def _create_callback_listener(self):
        from weakref import ref
        from random import randint
        from websockets.server import serve

        #create a weak reference to self, otherwise the cyclic reference
        #between the server and WebMOREST will prevent destruction due to
        #custom __dell__ method
        self_weakref = ref(self)
        async def _websocket_callback(websocket):
            async for message in websocket:
                self_weakref()._websocket_response_queue.append(message)

        #generate a random port between 50-60k, in the unreserved range
        self._callback_port = 50000 + randint(1,10000)
        self._callback_listener = await serve(_websocket_callback, port=self._callback_port)

        self._websocket_response_queue = []

    async def _process_callback_response(self):
        from base64 import b64decode
        TIMEOUT = 10

        json_msg = None
        for i in range(TIMEOUT):
            await asyncio.sleep(1)

            if len(self._websocket_response_queue) > 0:
                json_msg = self._websocket_response_queue.pop(0)
                break

        #Handle timeout waiting for response
        if json_msg is None:
            print("Timeout waiting for response from Javascript")
            return

        result = json.loads(json_msg)

        #create and return the image
        base64_image_data = result['imageURI'].split(",",2)[1]
        decoded_image_data = b64decode(base64_image_data);

        return EmbeddedImage(data=decoded_image_data)

if has_ipython:
    class EmbeddedImage(Image):
        """The EmbeddedImage class is a IPython-displayable image object with additional functionality.

    The EmbeddedImage class is a Jupyter-renderable image object, derived from IPython.display.image.   
        However, the EmbeddedImage also adds additional utility conversion methods.
        """
        def __init__(self, data):
            super().__init__(data)

        def save(self, filename):
            """Saves the EmbeddedImage to disk as a PNG-formatted image.

            This call saves the EmbeddedImage object to disk as PNG-formatted image.

            Arguments:
                filename(str): The path to the target PNG file. A "png" extension is added, if not provided.

            Returns:
                None
            """
            if not filename.endswith(".png"):
                filename += ".png"
            with open(filename, 'wb') as fp:
                fp.write(self.data)

        def to_pil_image(self):
            """Returns an equivalent Pillow (PIL) Image object.

            This call converts and returns and equivalent Pillow (PIL) Image representation of the
            current EmbeddedImage object, for further manipulation.

            Arguments:
                None

            Returns:
                A Pillow PIL.Image.Image object.
            """
            from PIL import Image
            from io import BytesIO

            return Image.open(BytesIO(self.data))

#
# lineshape functions
#

def _faddeeva(z):
    """
    Calculates the scaled complex complementary function in the complex plane.
    We use this to calculate voigt lineshapes.
    """
    if _faddeeva.run_yet == False:
        _faddeeva.run_yet = True
        _faddeeva.N = 1000
        _faddeeva.L = np.sqrt(_faddeeva.N / np.sqrt(2))
        # our basis set. 1000 elements hits a good blend of speed and accuracy.
        l = [
            5.11748989e-16,-1.44365777e-16,1.71205586e-16,1.43270169e-16,
            2.40509424e-16,9.34400028e-17,3.33586468e-16,2.07038704e-16,
            3.95030052e-16,-2.26565767e-17,2.99460336e-16,5.72632548e-16,
            1.29042294e-16,-7.07527120e-17,-5.62526370e-18,2.36711749e-16,
            1.02183724e-16,-4.34250382e-16,-8.07532865e-17,-4.96929924e-16,
            1.26045192e-16,-2.53796359e-16,-1.03766119e-16,-2.15858058e-16,
            -1.83552885e-16,-8.67481915e-17,-3.07549909e-16,-2.74584240e-16,
            -2.69389284e-17,-4.24362029e-16,-5.95060089e-16,-3.70830265e-16,
            2.29567357e-16,7.09903912e-17,-9.60967179e-16,2.56731866e-16,
            -4.28826105e-16,-4.30205991e-16,-5.08718759e-16,-2.72358486e-16,
            -2.89119580e-16,-3.97432513e-16,-4.35239789e-16,-8.06482626e-17,
            -8.25507147e-16,-3.76087656e-16,-8.24193610e-16,-5.49494587e-16,
            -6.65608655e-16,-7.53824209e-16,-7.22452074e-16,-3.57335854e-16,
            -2.98311037e-16,-4.14104958e-16,-2.58059335e-16,-7.98829398e-16,
            -3.86795717e-16,-2.37823897e-16,-1.83073068e-16,-8.98227362e-17,
            -5.28120565e-17,-4.52881008e-16,-1.81103394e-16,-8.56200133e-17,
            -1.22186640e-16,-5.41322089e-17,-7.24757378e-16,-3.50403658e-16,
            -1.42903007e-16,-1.86846592e-16,-3.94211076e-16,-5.10446457e-16,
            -2.41826709e-16,-1.21038373e-16,-3.79652685e-16,-3.19221360e-16,
            -3.57241318e-16,-3.08579376e-16,-1.28131320e-16,-3.12949918e-16,
            -2.46392992e-16,-2.91414183e-16,-2.85635470e-16,-8.72117464e-17,
            -5.38404011e-17,-7.88752966e-17,8.44277161e-17,2.10083596e-17,
            1.82773768e-17,-4.62896364e-16,-2.15480876e-16,-3.50123461e-16,
            -2.44328019e-16,-5.22369602e-16,-3.02177957e-16,-4.95661311e-16,
            -2.05232527e-16,-6.89780504e-16,-5.76999940e-16,-3.57086548e-16,
            -1.73695260e-16,-5.10360238e-16,-3.18226893e-16,-6.53936479e-16,
            -4.07209831e-16,-5.23531607e-16,-6.25241467e-16,-5.59616421e-16,
            -5.05190494e-16,-4.95920116e-16,5.91918728e-17,-4.24242069e-16,
            -4.26716888e-16,-1.94214030e-16,-3.91975316e-16,1.89855222e-17,
            -8.41436616e-17,-1.91135361e-16,1.17185773e-16,1.70875441e-17,
            -7.82465278e-17,-4.50946865e-16,-3.49996280e-16,-3.61639701e-16,
            -1.44123098e-16,-4.53945169e-16,-1.19604860e-16,-1.05312368e-16,
            -1.05598414e-16,-1.98885939e-16,-1.60492266e-16,-5.06892532e-17,
            -2.08435369e-16,-1.15672143e-16,-2.28953471e-16,-2.10576416e-16,
            -1.43268468e-16,-3.93351320e-16,-3.19012003e-16,-2.86881044e-16,
            -3.09187106e-16,4.85144017e-17,-1.43142304e-17,-2.05880804e-16,
            -2.88573343e-16,-2.34476402e-16,-4.24449546e-16,-3.15047863e-16,
            7.15863776e-18,-9.40085268e-17,-3.41068217e-16,-5.81558958e-16,
            -1.23060165e-16,-2.29925794e-16,-1.00051620e-16,2.60549021e-16,
            -1.95855091e-16,-6.47544512e-16,-2.11951657e-16,1.68350302e-16,
            -3.31451746e-16,-9.37946003e-17,-5.38246225e-17,2.45588357e-16,
            -1.55116503e-16,1.47231294e-16,3.32452583e-17,-1.15883349e-16,
            -6.26556401e-17,-4.11199133e-16,3.40065530e-16,2.76793021e-16,
            4.41447793e-16,5.24289805e-16,2.00946326e-16,3.90427144e-16,
            1.15328785e-16,1.07955299e-17,-2.17963342e-17,4.93958279e-16,
            2.49313066e-17,-1.32566816e-16,4.10357049e-16,-4.52822565e-16,
            4.07881112e-16,-7.92449589e-17,1.19915180e-16,1.39818533e-15,
            1.00809312e-17,-4.43575229e-16,-5.06216625e-17,4.14292705e-17,
            3.96859128e-17,-8.34232666e-16,9.11190986e-16,9.32038663e-16,
            8.84033937e-18,6.99303277e-18,9.01104015e-16,9.15275917e-16,
            0.00000000e00,9.09494702e-16,0.00000000e00,-9.09494702e-16,
            0.00000000e00,-9.09494702e-16,-9.09494702e-16,0.00000000e00,
            -9.09494702e-16,0.00000000e00,0.00000000e00,-4.54747351e-16,
            -4.54747351e-16,0.00000000e00,0.00000000e00,4.54747351e-16,
            4.54747351e-16,0.00000000e00,4.54747351e-16,0.00000000e00,
            0.00000000e00,0.00000000e00,0.00000000e00,4.54747351e-16,
            0.00000000e00,4.54747351e-16,4.54747351e-16,-4.54747351e-16,
            0.00000000e00,0.00000000e00,-4.54747351e-16,-4.54747351e-16,
            0.00000000e00,2.27373675e-16,-2.27373675e-16,-2.27373675e-16,
            0.00000000e00,-2.27373675e-16,-3.41060513e-16,-2.27373675e-16,
            -1.13686838e-16,-2.27373675e-16,0.00000000e00,5.68434189e-17,
            5.68434189e-17,3.97903932e-16,1.70530257e-16,-2.27373675e-16,
            1.70530257e-16,0.00000000e00,3.12638804e-16,1.42108547e-17,
            -1.13686838e-16,1.98951966e-16,9.94759830e-17,9.94759830e-17,
            1.20792265e-16,3.41060513e-16,2.62900812e-16,1.06581410e-16,
            2.73558953e-16,2.13162821e-17,2.87769808e-16,1.81188398e-16,
            4.19220214e-16,3.90798505e-17,2.38031816e-16,1.49213975e-16,
            4.86721774e-16,6.03961325e-17,3.49054119e-16,1.88737914e-16,
            3.00204306e-16,4.88498131e-17,9.72555370e-17,5.17141885e-16,
            1.27453603e-16,4.18998169e-16,4.35429470e-16,2.03947970e-16,
            3.28403971e-16,7.09432513e-17,2.75390821e-16,1.28230759e-16,
            1.38278278e-16,1.62314606e-16,1.17683641e-16,-7.49122986e-17,
            -4.42562653e-17,2.25021390e-16,5.67809688e-17,-9.29117894e-17,
            4.77465290e-17,-4.95159469e-17,-7.98319744e-17,-1.82109536e-16,
            1.66366920e-16,-1.86119349e-16,1.35362208e-16,-3.26893894e-16,
            1.89110880e-16,8.02986150e-17,2.42919400e-16,-1.88988365e-16,
            1.09200626e-16,-1.55745100e-16,-1.23230690e-16,-7.49633103e-17,
            -1.58868199e-16,-5.36516361e-17,2.77595573e-16,2.81580071e-16,
            -2.95155908e-16,-2.48784798e-16,2.91340472e-16,1.36892539e-16,
            1.70318153e-16,1.73748269e-16,4.65475589e-17,-2.31324207e-16,
            1.83833839e-17,-6.04137894e-17,4.80069234e-17,-2.85632380e-16,
            3.67524426e-17,-4.74434771e-17,-3.17576294e-16,-1.71678676e-16,
            -1.08599054e-16,-2.18406185e-16,1.85501493e-16,-1.46516971e-17,
            -9.07895605e-17,-7.19678890e-17,1.53856704e-16,-1.40846832e-16,
            7.20265739e-17,-2.54008979e-16,-1.23325143e-16,2.75474757e-16,
            2.32616486e-16,-1.75463698e-16,9.79362317e-17,2.20669333e-16,
            -2.29810374e-16,-7.95069634e-17,2.87994117e-16,3.12697006e-16,
            3.14586804e-16,1.79021616e-16,2.06952162e-17,-2.67293573e-16,
            3.45231230e-16,8.68326886e-17,2.65629639e-16,3.06821693e-18,
            1.34860677e-16,2.74418053e-16,-3.04162528e-16,1.09786189e-16,
            -1.54948449e-17,-3.43520294e-16,-8.60630571e-17,-3.28755503e-16,
            -2.06357180e-16,-7.70834219e-16,-4.48670877e-16,-4.21195874e-16,
            -3.33542439e-16,-1.12012549e-16,1.31482158e-16,-9.05916732e-17,
            -1.88320054e-16,-2.71973298e-16,-1.85779885e-16,-2.41487719e-16,
            -3.34298416e-16,-1.26864283e-16,-1.07737460e-16,-3.00912980e-16,
            -5.14639839e-16,-3.53320333e-16,-5.69661721e-16,-1.64073995e-16,
            -1.61323191e-16,-6.91875273e-16,2.10402594e-17,-4.97408214e-16,
            -9.58387029e-17,-4.71724194e-16,-2.64915700e-16,-3.20381256e-16,
            -1.81528269e-16,-3.63661361e-16,-3.33501787e-16,-4.82454667e-16,
            1.92955199e-17,-2.70836693e-16,3.39983475e-17,6.18997114e-17,
            -1.02320106e-16,1.27057441e-16,8.31854263e-17,-1.18884147e-16,
            9.89208773e-17,2.55999309e-16,-1.28411687e-17,1.37041750e-16,
            1.06258503e-16,4.81342042e-16,4.98521006e-16,2.55381445e-16,
            2.54674725e-16,2.62261848e-16,3.83584674e-16,1.89662976e-16,
            1.26359468e-16,3.08514032e-16,2.58755647e-16,2.87385786e-16,
            8.62079097e-17,2.85730122e-16,1.60530531e-16,2.12208599e-16,
            -7.50533882e-17,1.03721015e-16,-9.44620129e-17,-1.25196451e-17,
            1.83989433e-16,1.02092358e-16,1.23199547e-16,3.12924987e-16,
            7.94899735e-18,3.13515155e-17,-1.91924262e-16,-1.57024233e-16,
            -1.16563275e-16,1.01280507e-16,-3.14811048e-16,-1.99895021e-16,
            3.17185157e-17,3.72378215e-16,-2.48438099e-17,-1.96408130e-16,
            2.19875515e-16,-1.48259617e-16,-1.88755403e-16,6.10412835e-17,
            -7.97417495e-17,1.04554694e-16,-1.34343584e-16,1.57394697e-16,
            -2.97867426e-16,9.44191922e-17,-3.12413672e-16,1.09925848e-16,
            -1.70858155e-16,1.22319748e-16,-2.39270244e-16,2.99282075e-16,
            2.71551291e-16,1.51896598e-16,-1.91045098e-16,3.37244715e-16,
            -1.68447924e-16,2.78788148e-16,-1.02388408e-16,2.28266264e-16,
            -1.06314013e-16,7.49857205e-17,6.80150911e-17,2.62399291e-16,
            2.93062592e-16,6.72930693e-16,1.23409884e-16,7.80241772e-17,
            1.23935426e-16,7.42401592e-17,-4.97733202e-17,2.24872387e-17,
            3.13006754e-17,4.36894318e-16,-2.73584271e-17,5.34106732e-16,
            3.04015329e-17,3.55236272e-16,2.00061692e-16,2.35008822e-17,
            2.00115055e-16,7.50216609e-16,1.71467707e-16,5.48936595e-16,
            6.59987339e-16,9.11465756e-16,3.27550321e-16,3.16454926e-16,
            3.25061464e-16,3.92881805e-16,4.45080470e-16,4.34813674e-16,
            2.86276929e-16,2.80084273e-16,4.02814643e-16,2.86153600e-16,
            1.46638302e-16,2.34169964e-16,-3.36764594e-17,1.72043602e-16,
            3.94568392e-16,1.84240100e-16,1.58638568e-16,-6.67371223e-17,
            2.14683219e-16,-4.10907209e-17,-5.60176818e-18,-4.23445380e-16,
            1.13835939e-18,-1.09095088e-16,8.20242358e-17,8.94645890e-17,
            1.93399044e-16,3.99021608e-17,-1.82013746e-16,6.18526657e-16,
            -1.11938105e-16,6.66551783e-16,5.13967366e-16,5.58363111e-16,
            -4.19435265e-18,-3.54000381e-16,1.01030703e-16,4.22960946e-16,
            2.42257871e-16,1.01132651e-16,1.82876993e-16,-9.86957381e-17,
            3.56039675e-16,1.05496299e-16,3.44095847e-16,5.75735467e-16,
            2.24941492e-16,2.69783032e-16,1.92864050e-16,-9.74377652e-18,
            2.79461094e-16,-3.94524145e-16,6.85116549e-17,-3.18711202e-16,
            -7.88669123e-17,7.99601369e-17,-2.31458426e-17,-2.50800230e-16,
            -7.86084747e-17,-4.74833060e-16,-4.36565773e-17,-1.55929470e-16,
            -4.05522987e-16,-3.59094184e-16,-2.55120726e-16,-4.05726600e-16,
            -2.13699502e-16,-5.41348764e-16,-4.78030787e-17,-2.58327801e-16,
            -3.46581471e-16,-3.46533290e-16,-8.53057559e-17,-5.38831280e-16,
            -3.46786352e-16,-4.32363655e-16,-1.68813053e-16,-7.17961227e-17,
            -3.91976466e-16,-2.55961277e-16,-6.32428739e-17,-2.99788312e-16,
            5.13471358e-17,-4.10951740e-16,-1.03668319e-17,-2.33628706e-16,
            -3.38590834e-16,-5.28009955e-18,-6.29904955e-17,-2.06798096e-16,
            -2.06115411e-16,-5.30012252e-16,-8.60235170e-17,-3.79126886e-16,
            -3.93774310e-16,-1.23453191e-16,-1.98039359e-16,-2.99884806e-16,
            -1.70348792e-16,-5.75530462e-16,-1.90399233e-17,-1.33260936e-16,
            -2.41764387e-16,-2.41057218e-16,2.74137576e-17,-1.43504070e-16,
            -1.79498040e-16,-1.49035292e-16,-5.13045291e-17,7.64957220e-17,
            -9.01996753e-18,7.79047747e-17,8.01635709e-17,1.01525911e-16,
            3.24917016e-16,1.64160518e-16,1.22226009e-16,5.58281902e-16,
            7.64857413e-17,2.02497667e-16,8.65193004e-17,3.72152535e-16,
            -9.26868752e-18,-2.09224351e-16,-8.47794702e-17,-1.25922233e-16,
            1.29086358e-16,2.89461144e-16,-8.20626177e-17,-5.16486509e-17,
            1.83191796e-16,-3.06674860e-16,-1.13915329e-16,3.80596575e-16,
            -3.28275082e-16,1.10666724e-16,-5.99813539e-17,1.05195582e-16,
            -1.75628122e-16,-3.65824066e-16,-4.36305437e-16,-1.34170680e-16,
            -2.35694163e-18,-8.44147857e-17,-2.29387585e-16,-2.49491085e-16,
            -3.82957891e-16,-2.01082319e-16,-3.69520171e-16,3.08359859e-16,
            -1.99895640e-17,-3.32817349e-16,-1.20815203e-16,-3.95566702e-18,
            -4.24507796e-16,-3.33867325e-16,-6.50492639e-16,-4.67244932e-16,
            -6.40278657e-17,-1.99413595e-16,-6.38794849e-17,-4.86309451e-16,
            -3.90516920e-16,-5.53476004e-16,-4.25387534e-16,-5.07859220e-16,
            1.50184194e-16,-1.56593179e-16,-5.77023883e-17,-1.20813224e-16,
            -2.42609780e-16,-6.96228162e-16,-2.31425493e-16,-5.63834410e-16,
            -3.28654446e-16,-3.29201011e-16,1.15017889e-16,-5.36343420e-16,
            -2.25728055e-17,-4.08400873e-16,-7.62532358e-18,-5.63480342e-16,
            2.29275694e-17,-3.86463027e-16,-1.19440287e-16,-1.12034603e-17,
            -4.48245375e-16,-8.71150653e-17,-3.59698822e-16,7.63701580e-16,
            -2.09249540e-16,-7.29027711e-17,4.34806301e-16,2.79370416e-16,
            4.35781459e-16,9.68543292e-17,1.82341529e-16,4.66259454e-16,
            4.58752443e-16,-5.47309304e-16,4.82142613e-16,6.60132335e-16,
            4.61280949e-16,-3.13067390e-16,1.92698504e-16,1.04964129e-16,
            -8.98832392e-17,-3.42289455e-16,3.43710315e-16,3.40297977e-17,
            2.34400799e-16,3.56171595e-17,-1.35737919e-16,4.13360932e-16,
            9.28909624e-17,-5.26283763e-17,5.39552046e-16,2.63123975e-16,
            1.77400491e-16,1.60163316e-16,1.73522799e-16,2.60524046e-16,
            3.91736558e-16,1.22245854e-16,5.72475581e-16,-2.79943119e-17,
            5.39626522e-16,4.69224371e-16,1.79053135e-16,4.94826390e-16,
            3.39932067e-16,8.38290822e-17,2.83931853e-16,5.55942954e-16,
            4.19747676e-16,2.79124937e-16,2.03558902e-16,4.24519122e-16,
            1.02658980e-16,1.89197331e-17,3.63112861e-16,1.41263763e-16,
            -6.39833244e-17,2.94156130e-16,1.19279922e-16,2.62537867e-16,
            9.23250107e-17,9.54340873e-17,2.02657914e-16,8.56837549e-17,
            1.09912242e-16,3.25830034e-16,-6.06707638e-17,1.19561917e-16,
            1.82940837e-18,-4.63814691e-17,-1.76004402e-16,-1.14268787e-16,
            -1.99388849e-16,-2.34993921e-16,-2.91227483e-16,7.53550548e-18,
            4.82690083e-18,-2.38575495e-16,-2.44652589e-16,-8.24120125e-17,
            -1.33320590e-16,-2.00054414e-16,-1.43372915e-16,1.89338899e-16,
            -3.10018714e-16,-1.46340691e-16,-1.07599704e-16,-1.64066751e-16,
            -2.17562644e-16,-1.17636359e-16,-1.86483075e-16,5.34358570e-17,
            -4.22094388e-17,1.49639967e-16,-9.19369910e-17,6.43735552e-17,
            -4.95497319e-17,3.33550953e-16,-5.58797396e-18,1.08044533e-17,
            -5.68782134e-17,-1.09699521e-16,2.02816822e-17,6.57529483e-18,
            -5.62985774e-17,1.37422525e-16,3.68137873e-16,2.93855626e-16,
            4.60911681e-16,2.79558527e-16,1.93645149e-16,4.29339673e-16,
            3.94346119e-16,-9.11980916e-17,2.08587798e-16,4.60632308e-16,
            2.46253693e-16,2.94939706e-16,2.89601071e-16,2.36630408e-16,
            3.40090024e-16,2.08679525e-16,1.92263017e-16,9.71798469e-17,
            2.75039790e-16,4.35625730e-16,3.44388483e-16,3.13739000e-16,
            2.67825858e-16,5.23555689e-16,7.02254341e-17,1.24864649e-16,
            3.20139668e-16,2.33491483e-16,2.19996198e-16,3.10765864e-16,
            1.92283246e-16,4.58564011e-16,5.97928541e-16,1.65336064e-16,
            1.97369721e-16,4.79474407e-16,4.74556351e-16,-2.72567462e-17,
            4.84030144e-16,2.35944695e-16,-1.64178854e-16,2.08598406e-16,
            4.78048738e-16,-1.07186669e-16,2.72374315e-16,1.30982162e-16,
            6.19721697e-16,1.84166717e-16,2.19916975e-16,-8.38157837e-17,
            3.10783706e-16,1.43651243e-16,8.32086938e-16,-8.60950101e-17,
            1.12719684e-15,1.25055521e-15,1.59161573e-15,2.61479727e-15,
            5.34328137e-15,8.24229573e-15,1.30739863e-14,2.09752216e-14,
            3.33102435e-14,5.24096322e-14,8.29913915e-14,1.30512490e-13,
            2.04465778e-13,3.19687388e-13,4.96527264e-13,7.69091457e-13,
            1.18768639e-12,1.82723170e-12,2.80164159e-12,4.28093472e-12,
            6.51965593e-12,9.89587079e-12,1.49690322e-11,2.25677468e-11,
            3.39091173e-11,5.07809830e-11,7.57933947e-11,1.12751053e-10,
            1.67175699e-10,2.47052924e-10,3.63894571e-10,5.34237415e-10,
            7.81753258e-10,1.14021130e-09,1.65761999e-09,2.40199471e-09,
            3.46936706e-09,4.99485579e-09,7.16792849e-09,1.02533485e-08,
            1.46198336e-08,2.07791178e-08,2.94389945e-08,4.15750919e-08,
            5.85276356e-08,8.21314254e-08,1.14889782e-07,1.60206498e-07,
            2.22693985e-07,3.08581163e-07,4.26251360e-07,5.86949080e-07,
            8.05705175e-07,1.10254346e-06,1.50404848e-06,2.04539498e-06,
            2.77296513e-06,3.74771110e-06,5.04945887e-06,6.78239587e-06,
            9.08204151e-06,1.21240672e-05,1.61354139e-05,2.14082509e-05,
            2.83174350e-05,3.73422599e-05,4.90934463e-05,6.43464991e-05,
            8.40827711e-05,1.09539808e-04,1.42272822e-04,1.84229443e-04,
            2.37840239e-04,3.06127873e-04,3.92838172e-04,5.02596823e-04,
            6.41095903e-04,8.15314926e-04,1.03378162e-03,1.30687819e-03,
            1.64719925e-03,2.06996828e-03,2.59351969e-03,3.23985416e-03,
            4.03527510e-03,5.01111418e-03,6.20455414e-03,7.65955651e-03,
            9.42790170e-03,1.15703481e-02,1.41579155e-02,1.72732972e-02,
            2.10124030e-02,2.54860316e-02,3.08216711e-02,3.71654197e-02,
            4.46840156e-02,5.35669618e-02,6.40287248e-02,7.63109798e-02,
            9.06848724e-02,1.07453255e-01,1.26952855e-01,1.49556315e-01,
            1.75674058e-01,2.05755892e-01,2.40292299e-01,2.79815316e-01,
            3.24898926e-01,3.76158879e-01,4.34251842e-01,4.99873794e-01,
            5.73757579e-01,6.56669521e-01,7.49405043e-01,8.52783210e-01,
            9.67640138e-01,1.09482124e00,1.23517231e00,1.38952936e00,
            1.55870741e00,1.74348805e00,1.94460614e00,2.16273548e00,
            2.39847384e00,2.65232736e00,2.92469468e00,3.21585089e00,
            3.52593174e00,3.85491824e00,4.20262214e00,4.56867248e00,
            4.95250359e00,5.35334499e00,5.77021329e00,6.20190671e00,
            6.64700218e00,7.10385565e00,7.57060543e00,8.04517909e00,
            8.52530380e00,9.00852024e00,9.49220006e00,9.97356678e00,
            1.04497200e01,1.09176625e01,1.13743304e01,1.18166252e01,
            1.22414481e01,1.26457352e01,1.30264942e01,1.33808408e01,
            1.37060347e01,1.39995149e01,1.42589331e01,1.44821848e01,
            1.46674378e01,1.48131571e01,1.49181262e01,1.49814637e01,
        ]
        a = np.array(l)
        a = np.flip(a)
        _faddeeva.vals = a
        _faddeeva.poly = np.polynomial.polynomial.Polynomial(a)

    Z = (_faddeeva.L + 1j * z) / (_faddeeva.L - 1j * z)
    p = _faddeeva.poly(Z)
    w = 2 * p / (_faddeeva.L - 1j * z)**2 + (1 / np.sqrt(np.pi)) / (_faddeeva.L - 1j * z)

    return(w)

_faddeeva.run_yet = False
_faddeeva.vals = None
_faddeeva.L = None
_faddeeva.N = None
_faddeeva.poly = None

def _arb_voigt(center, intensity, ratio, peak_width):
    """
    Use the Faddeeva function to calculate a voigt line shape. See
    https://en.wikipedia.org/wiki/Voigt_profile#The_uncentered_Voigt_profile
    """

    def _voigt_decoder(q, k):
        """
        Takes the FWHM (k) and a ratio (q) and determines the values of gamma and sigma.

        Accurate to within around 1.2%.
        """
        f_l = (-k*(q**2) + (-1 + q)**2 * np.sqrt(((k**2)*(q**2) * (4 - 8 * q + 5 * (q**2)))/(-1 + q)**4))/(2 * (-1 + q)**2)
        f_g = (k * (q**2) - (-1 + q)**2 * np.sqrt(((k**2) * (q**2) * (4 - 8 * q + 5 * (q**2)))/(-1 + q)**4))/(2 * (-1 + q) * q)


        gamma = f_l/2 # because gamma = FWHM/2
        sigma = f_g / (2 * np.sqrt(2*np.log(2)))

        return(gamma,sigma)

    from math import sqrt, pi

    gamma, sigma = _voigt_decoder(ratio, peak_width)
    denom = sigma * sqrt(2 * pi) # denomonator
    z = lambda x: _faddeeva((x - center + gamma*1j)/(sqrt(2) * sigma)) # Define z(x) as numerator, more or less
    l = lambda x: intensity * ((z(x).real)/denom) # define the actual voigt function

    return l

def voigt_line(center, intensity, width=10, q=0.5, start=0, stop=4000, step=1):
    """Calculate a voigt lineshape

    This function returns a pair of numpy arrays that define a voigt line.

    Arguments:
    	center(float): the center point of the line
    	intensity(float): the area under the line
    	width(float,optional): the full width half max of the desired line
    	q(float,optional): the ratio of gaussian to lorentzian
    	start(float,optional): the starting point of the returned array
    	stop(float,optional): the ending point of the returned array
    	step(float,optional): the step between points of the returned array

    Returns:
    	(x,y): a tuple of the x and y numpy arrays of the specified line
    """
    x = np.arange(start=start, stop=stop, step=step)
    vfunc = np.vectorize(_arb_voigt(center, intensity, q, width))
    return((x,vfunc(x)))

def _arb_gaussian(center, intensity, width=10):
    """
    Return a gaussian with an arbitrary height and intensity, with sigma being determined by calculating
    it from our FWHM peak width.
    """
    from math import sqrt, pi, exp, log

    sigma = (width / (2 * sqrt(2 * log(2))))
    l = lambda x: intensity * (1/sigma*sqrt(2*pi)) * exp(-((x-center)**2/(2*sigma**2)))

    return l

def gauss_line(center, intensity, width=10, start=0, stop=4000, step=1):
    """Calculate a gaussian lineshape

    This function returns a pair of numpy arrays that define a gaussian line.

    Arguments:
    	center(float): the center point of the line
    	intensity(float): the area under the line
    	width(float,optional): the full width half max of the desired line
    	start(float,optional): the starting point of the returned array
    	stop(float,optional): the ending point of the returned array
    	step(float,optional): the step between points of the returned array

    Returns:
    	(x,y): a tuple of the x and y numpy arrays of the specified line
    """
    x = np.arange(start=start, stop=stop, step=step)
    vfunc = np.vectorize(_arb_gaussian(center, intensity, width))
    return((x,vfunc(x)))

def _arb_lorentz(center, intensity, width=10):
    """
    Return a lorentzian with an arbitrary height and intensity, with gamma being calculated from our
    FWHM peak width.
    """
    from math import pi

    gamma = (width / 2)
    l = lambda x: (intensity/pi) * (gamma/((x-(center))**2 + gamma**2))

    return l

def lorentz_line(center, intensity, width=10, start=0, stop=4000, step=1):
    """Calculate a lorentzian lineshape

    This function returns a pair of numpy arrays that define a lorentzian line.

    Arguments:
    	center(float): the center point of the line
    	intensity(float): the area under the line
    	width(float,optional): the full width half max of the desired line
    	start(float,optional): the starting point of the returned array
    	stop(float,optional): the ending point of the returned array
    	step(float,optional): the step between points of the returned array

    Returns:
    	(x,y): a tuple of the x and y numpy arrays of the specified line
    """
    x = np.arange(start=start, stop=stop, step=step)
    vfunc = np.vectorize(_arb_lorentz(center, intensity, width))
    return((x,vfunc(x)))

#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""This module contain the collection of astrobject"""
import numpy as np
import warnings
from astropy.table import Table
        
from .baseobject import BaseObject
from .instruments import instrument as inst
from ..utils.tools import kwargs_update
from ..utils.shape import draw_polygon

__all__ = ["ImageCollection"]

#######################################
#                                     #
# Base Collection                     #
#                                     #
#######################################
class BaseCollection(BaseObject):
    """
    """
    __nature__ = "Collection"

    _properties_keys = ["handler"]
    
    def __init__(self):
        """
        """
        self.__build__()
        return 

    # ========================== #
    # = Generic Methods        = #
    # ========================== #
    def remove(self,id):
        """This methods enable to remove the given data from the current instance"""
        self._test_source_(id)
        to_rm = self._handler.pop(id)
        del to_rm

    def rename(self,id,newid,force_it=False):
        """This methods enable to change the id with which the data is accessed.
        Remark: If the 'newid' already exists, an exception is raised except
        if force_it is set to true. In that a case, this will overwrite
        the 'newid' entry.
        """
        # -- Test if it is ok
        self._test_source_(id)
        if newid in self.list_id and not force_it:
            raise ValueError("the newid '%s' already exists. Set force_it to true to overwrite it")
        
        # -- Do the switch
        self._handler[newid] = self._handler.pop(id)

    # ----------------- #
    # - Getter        - #
    # ----------------- #

    # ----------------- #
    # - Setter        - #
    # ----------------- #

    # ========================== #
    # = Internal Tools         = #
    # ========================== #
    def _test_source_(self,source):
        """This methods tests if the given 'id' exists"""
        if source not in self.list_sources:
            raise ValueError("'%s' is not a known source "%source +"\n"\
                             "These are: "+", ".join(self.list_sources))
        return True
    
    # ========================== #
    # = Properties             = #
    # ========================== #
    # ---------------------
    # - Data Handlers
    @property
    def _handler(self):
        """
        This is where the data are recorded. Any data.
        """
        # - Handler are dictionnaries
        if self._properties["handler"] is None:
            self._properties["handler"] = {}
            
        return self._properties["handler"]

    @property
    def nsources(self):
        return len(self._handler.keys())
        
    def has_sources(self):
        return len(self._handler.keys()) > 0
    
    @property
    def list_sources(self):
        """This is the list of the known data id"""
        if not self.has_sources():
            raise AttributeError("no data loaded")
        
        return np.sort(self._handler.keys()).tolist()
    

# =============================== #
#                                 #
#  Astro-oriented BaseCollection  #
#                                 #
# =============================== #
class Collection( BaseCollection ):
    """
    """
    def __build__(self,*args,**kwargs):
        """
        """
        self._side_properties_keys.append("target")
        super(Collection,self).__build__(*args,**kwargs)
        
    # ----------------- #
    # - Setter        - #
    # ----------------- #
    def set_target(self,newtarget):
        """
        Change (or create) an object associated to the given image.
        This function will test if the object is withing the image
        boundaries (expect if *test_inclusion* is set to False).
        Set newtarget to None to remove the association between this
        object and a target
        """
        if newtarget is None:
            self._side_properties['target'] = None
            return
        
        # -- Input Test -- #
        if newtarget.__nature__ != "AstroTarget":
            raise TypeError("'newtarget' should be (or inherite) an AstroTarget")
        
        # -- Seems Ok -- #
        self._side_properties["target"] = newtarget.copy()

    def _test_id_(self,id_):
        """
        """
        return self._test_source_(id_)
    # ========================== #
    # = Properties             = #
    # ========================== #
    @property
    def ndata(self):
        return self.nsources
        
    def has_data(self):
        return self.has_sources()
    
    @property
    def list_id(self):
        """This is the list of the known data id (equivalent to list_sources)"""
        return self.list_sources
    # ---------------------
    # - Target
    @property
    def target(self):
        """The associated target if loaded"""
        return self._side_properties['target']
    
    def has_target(self):
        return self.target is not None

#######################################
#                                     #
# Image Collection                    #
#                                     #
#######################################
class ImageCollection( Collection ):
    """
    """
    _side_properties_keys = ["catalogue"]
    
    def __init__(self,images=None,empty=False,catalogue=None):
        """
        """
        self.__build__()
        if empty:
            return
        
        self.create(images,catalogue=catalogue)

        
    def create(self,images,catalogue=None):
        """
        Loop over the images end add them to the instance. See add_image
        """
        if "__iter__" not in dir(images):
            images = [images]
        # ---------------------------
        # - dealing with catalogues
        if catalogue is None:
            catalogue = True
        elif type(catalogue) is not bool: 
            self.set_catalogue(catalogue)

        [self.add_image(i_,load_catalogue=catalogue) for i_ in images
         if i_ is not None]

    def set_target(self,newtarget, set_to_images=True):
        """
        Change (or create) an object associated to the given image.
        This function will test if the object is withing the image
        boundaries (expect if *test_inclusion* is set to False).
        Set newtarget to None to remove the association between this
        object and a target

        set_to_images [bool]       If any images is loaded and this is within the image FoV
                                   shall we set the target to the image ?
        """
        super(ImageCollection,self).set_target(newtarget)
        if set_to_images:
            for id_ in self.list_id:
                if self.images[id_]["image"] is not None:
                    try:
                        self.images[id_]["image"].set_target(self.target)
                    except ValueError:
                        warnings.wanr("the new target is not in %s's FoV "%id_)
        
                    
        
    # ========================= #
    # = Images IO             = #
    # ========================= #
    def add_image(self,new_image,load_catalogue=True):
        """
        This method enables to save the given image in the self.images container (dict).
        To save speed and memory the given is saved as it is i.e., if its a filename
        the filename is recorded, if its an astrobject Image (or children) this Image
        is recorded. If its a file, it will be loaded only when needed.
        * Important * if a filename is given in input, this methods *TEST if the file
        corresponds to a known instrument*
        ( see astrobject's instrument.is_known_instrument_file )

        Parameters
        ----------
        new_image: [string or astrobject's Image (or children)]

        - option -

        load_catalogue: [bool]     run the 'download_catalogue' method to
                                   download the corresponding catalogue if
                                   it does not exist yet.
        Return
        ------
        Void
        """
        # ------------------------ #
        # What should be loaded  - #
        # ------------------------ #
        if type(new_image) == str:
            idloaded = self._add_image_file_(new_image)
        
        elif "__nature__" in dir(new_image) and new_image.__nature__ != "Image":
            idloaded = self._add_astroimage_(new_image)
        else:
            # -- Issue
            raise TypeError("the given new_image must be a image-file or an astrobject imnage")
        if load_catalogue:
            self.download_catalogue(id_=idloaded)
            

    def load_images(self,verbose=True):
        """
        """
        [self._load_image_(id_) for id_ in self.list_id
         if self.images[id_]["image"] is None]
        # - done
            
    # ========================== #
    # = Get                    = #
    # ========================== #
    def get_image(self,id,load_catalogue=True):
        """
        """
        self._test_id_(id)
        # --------------------
        # - image already exist
        if self.images[id]["image"] is None:
            self._load_image_(id)
            return self.get_image(id)
        
        im = self.images[id]["image"]
        
        # ---------------
        # Target
        if not im.has_target() and self.has_target():
            im.set_target(self.target)
        # ---------------
        # Catalogue
        if load_catalogue and self.has_catalogue() and not im.has_catalogue():
            # --- Check if the current catalogue is big enough
            im.set_catalogue(self.catalogue.copy())

        return im

    def get_subcatalogue(self, kind="all", isolated_only=False, stars_only=False):
        """
        Get a copy of a catalogue. If could be the entire catalogue (kind=None or kind="all")
        or the shared fov catalogue (kind="shared" or "union") or the combined fov catalogue
        (kind="combined" or "intersection")
        """
        if not self.has_catalogue():
            raise AttributeError("No Catalogue loaded")
        # ---------------
        # - Which mask
        if kind is None or kind.lower() in ["all"]:
            contours = None
        elif kind.lower() in ["shared","union"]:
            contours = self.contours_shared
        elif kind.lower() in ["combined","intersection"]:
            contours = self.contours_combined
        else:
            raise ValueError("I could not parse the given kind %s (must be 'all', 'shared' or 'combined')"%kind)
        # ---------------
        # - get the new catalogue
        return self.catalogue.get_subcatalogue(contours=contours,
                                               isolated_only=isolated_only,
                                               stars_only=stars_only)
    # --------------------- #
    # - Get Extraction     - #
    # --------------------- #
    def get_photopoints(self,ra,dec,radius, runits="arcsec",
                        ids=None):
        """
        """
        idused = self.list_id if ids is None else\
          [ids] if "__iter__" not in dir(ids) else ids

        
        
            
    # --------------------- #
    # - Get Target        - #
    # --------------------- #
    def get_target_ids(self,target=None):
        """
        This methods enable to access the list of 'data' ids that contains the given target.

        Parameters:
        ----------
        - options -
        target: [None/ AstroTarget]   If no target is given and a target has been set
                                      (set_target) the current target will be used.
                                      If you give here a target, it will use it *without*
                                      changing the current target.
                                      -> Error
                                      This method raise a ValueError is no target accessible.

        Return:
        -------
        list (ids)
        """
        # -----------------
        # - Target
        if target is None:
            if not self.has_target():
                raise ValueError("no target set to the instance and no input target")
            target = self.target
        elif "__nature__" not in dir(target) or target.__nature__ != "AstroTarget":
            raise TypeError("The given 'target' must be an astrobject AstroTarget")
        # -----------------
        # - ID information
        return [id_ for id_ in self.list_id
            if self.images[id_]["wcs"].coordsAreInImage(target.ra,target.dec)]
            
    def get_target_collection(self,target=None):
        """
        This modules enables to get a new ImageCollection containing only
        the images corresponding to the given target (target in the image FoV).

        Parameters:
        -----------

        - options -

        target: [None/ AstroTarget]   If no target is given and a target has been set
                                      (set_target) the current target will be used.
                                      If you give here a target, it will use it *without*
                                      changing the current target.
                                      -> Error
                                      This method raise a ValueError is no target accessible.
                                      (see self.get_target_ids)

        Return:
        -------
        ImageCollection
        """
        im = ImageCollection([self.images[id_]["file"]
                              for id_ in self.get_target_ids(target)])
        im.set_target(target)
        return im

    def get_target_photopoints(self,radius,runits="kpc",target=None,
                               onflight=False,**kwargs):
        """
        This modules enables to get a new ImageCollection containing only
        the images corresponding to the given target (target in the image FoV).

        Parameters:
        -----------

        radius_kpc: [float]           The aperture photometry radius in kpc.
                                      (kpc will be converted in pixels for every images)
                                      
                                      
        - options -

        target: [None/ AstroTarget]   If no target is given and a target has been set
                                      (set_target) the current target will be used.
                                      If you give here a target, it will use it *without*
                                      changing the current target.
                                      -> Error
                                      This method raise a ValueError is no target accessible.
                                      (see self.get_target_ids)

        onflight: [bool]              Use this to avoid to load the images in the current instance
                                      If True, this will instead load a copy of the current instance
                                      using 'get_target_collection' which will then be delaited.
                                      -> Use this to save cach-memory once the method is finished.
        
        -- other options --
        
        kwargs goes to get_target_photopoints (-> get_aperture), including notably:
               aptype, subpix, ellipse_args, annular_args

           
        Return:
        -------
        PhotoPointCollection
        """
        if not onflight:
            ids = self.get_target_ids(target=target)
            images = [self.get_image(_id,load_catalogue=False)
                      for _id in ids]
        else:
            target_imcoll = self.get_target_collection(target=target)
            images = [target_imcoll(_id,load_catalogue=False)
                      for _id in target_imcoll.list_id]

        
        photopoints = PhotoPointCollection(photopoints=[image_.get_target_photopoint(radius=radius,runits=runits,
                                            **kwargs) for image_ in images])
        
        # ------------------------------
        # - Shall we delete the files ?
        if onflight:
            del images
            del target_imcoll
            
        return photopoints
    # ========================== #
    # = Set                    = #
    # ========================== #
    # --------------------- #
    # - Catalogue Methods - #
    # --------------------- #
    def set_catalogue(self,catalogue,force_it=False):
        """
        """
        if self.has_catalogue() and force_it is False:
            raise AttributeError("'catalogue' already defined"+\
                    " Set force_it to True if you really known what you are doing")

        if "__nature__" not in dir(catalogue) or catalogue.__nature__ != "Catalogue":
            raise TypeError("the input 'catalogue' must be an astrobject catalogue")
        # Important:
        # No WCS solution loaded here, this will be made image by image
        # --------
        # - set it
        self._side_properties["catalogue"] = catalogue


    def download_catalogue(self,id_=None,
                           source="sdss",
                           **kwargs):
        """
        """
        loop_id = self.list_id if id_ is None else [id_] if "__iter__" not in dir(id_) else id_
        for id_ in loop_id:
            # -- Loop over the images, check what is needed
            if not self.has_catalogue() or \
              not self.catalogue.contours.contains(self.images[id_]["wcs"].contours):
                new_cat = self._get_id_catalogue_(id_,source=source,**kwargs)
                if not self.has_catalogue():
                    self.set_catalogue(new_cat)
                else:
                    self.catalogue.merge(new_cat)

    
    # ========================== #
    # = Show                   = #
    # ========================== #
    def show_skypatches(self,ax=None,
                        savefile=None,show=True,
                        fc="None",ec="k",
                        targetprop={},
                        show_catalogue=True,show_target=True,
                        **kwargs):
        """
        Plot On the sky the 
        """
        from ..utils.mpladdon import wcsplot,figout,mpl
        
        # ----------------------
        # -   Axis Init
        if ax is None:
            fig = mpl.figure(figsize=[8,8])
            ax  = fig.add_axes([0.1,0.1,0.8,0.8])
        elif "imshow" not in dir(ax):
            raise TypeError("The given 'ax' most likely is not a matplotlib axes. "+\
                             "No imshow available")
        else:
            fig = ax.figure

        # ----------------------
        # -  loop over the images
        _prop = kwargs_update({"zorder":5},**kwargs)
        pl = [ax.wcsplot(self.images[id_]["wcs"],fc=fc,ec=ec,**_prop)
              for id_ in self.list_id if self.images[id_]["wcs"] is not None]

        # ----------------------
        # - Catalogue
        if self.has_catalogue() and show_catalogue:
            self.catalogue.display(ax,zorder=3)
            draw_polygon(ax,self.contours_shared,zorder=4,fc=mpl.cm.Greens(0.4,0.3))
            
        # ----------------------
        # - Target
        if self.has_target() and show_target:
            default_markerprop = {
                "marker":"o","mfc":"w",
                "mec":"k","mew":1,"zorder":12,
                "scalex":False,"scaley":False
                }
            prop = kwargs_update(default_markerprop,**targetprop)
            pl = ax.plot(self.target.ra,self.target.dec,**prop)
            
        # ----------------------
        # -  output
        fig.figout(savefile=savefile,show=show)
    
    # ========================== #
    # = INTERNAL               = #
    # ========================== #
    def _get_id_catalogue_(self,id_,source="sdss",radius_degree=None,**kwargs):
        """
        """
        print "downloading catalogue for %s"%id_
        radec = "%s %s"%(self.images[id_]['wcs'].central_coords[0],
                         self.images[id_]['wcs'].central_coords[1])
        img_radius= self.images[id_]['wcs'].diag_size/ 1.5
        radius = img_radius if radius_degree is None or radius_degree<img_radius \
          else radius_degree
          
        return inst.catalogue(source=source,radec=radec,radius="%sd"%radius,
                             **kwargs)
    # =============== #
    # = IO images   = #
    # =============== #
    def _add_image_file_(self,imagefile):
        """
        """
        # -- Load a file
        if not inst.is_known_instrument_file(imagefile):
            raise TypeError("the given new_image file is not an image of a known instrument")

        ID = imagefile.split("/")[-1]
        self.images[ID] = {
            "file":imagefile,
            "image":None
            }
        try:
            self.images[ID]["wcs"] = inst.get_instrument_wcs(imagefile)
        except:
            print "WARNING Failure to load the wcs solution"
            self.images[ID]["wcs"] = None
            
        return ID
    
    def _add_astroimage_(self,astroimage):
        """
        """
        # -- Load an image
        if new_image.filename is not None:
            ID = new_image.filename.split("/")[-1]
        else:
            ID = "image%d"%len(self.images.keys())

        self.images[ID] = {
            "file":new_image.filename,
            "image":new_image,
            "wcs":new_image.wcs if new_image.has_wcs() else None
            }
        return ID
        
    def _load_image_(self,id):
        """
        """
        self.images[id]["image"] = inst.instrument(self.images[id]["file"])
        
    # ========================== #
    # = Properties             = #
    # ========================== #    
    @property
    def images(self):
        """
        """
        return self._handler

    @property
    def _imageids(self):
        print "_imageids to be changed to self.list_id"
        return self.list_id
    
    # -- Catalogue
    @property
    def catalogue(self):
        return self._side_properties['catalogue']

    def has_catalogue(self):
        return not self.catalogue is None 

    # ------------------ #
    # - On flight prop - #
    # ------------------ #
    @property
    def bandnames(self):
        """This returns an array of the recorded images' bandname"""
        # -- This might be included in the add/remove image tools
        return [self.images[id_]["image"].bandname
                  if self.images[id_]["image"] is not None \
                  else inst.which_band_is_file(self.images[id_]["file"])
                for id_ in self.list_id]

    # ------------------
    # - Shapely Based
    @property
    def contours_shared(self):
        """ returns the contour (shapely polygon) of the shared covered sky area"""
        for i,d in enumerate(self.images.values()):
            fov = d["wcs"].contours if i == 0 else\
              fov.intersection(d["wcs"].contours)
        return fov
    
    @property
    def contours_combined(self):
        """ returns the contour (shapely polygon) of the combined covered sky area"""
        for i,d in enumerate(self.images.values()):
            fov = d["wcs"].contours if i == 0 else\
              fov.union(d["wcs"].contours)
        return fov
    
#######################################
#                                     #
# Image Collection -> SED SOURCE      #
#                                     #
#######################################
class PhotoPointCollection( Collection ):
    """
    """
    
    def __init__(self, photopoints=None,filein=None,empty=False,**kwargs):
        """
        """
        self.__build__()
        if empty:
            return
        
        if filein is not None:
            self.load(filein,**kwargs)
            
        if photopoints is not None:
            self.create(photopoints,**kwargs)
    # =============================== #
    # = Main Methods                = #
    # =============================== #

    # ------------------- #
    # - I/O PhotoPoint  - #
    # ------------------- #
    def create(self,photopoints,ids=None):
        """
        """
        if "__iter__" not in dir(photopoints):
            photopoints = [photopoints]
        if "__iter__" not in dir(ids):
            ids = [ids]*len(photopoints)
            
        if len(ids) != len(photopoints):
            raise ValueError("photopoints and ids must have the same size")
        
        [self.add_photopoint(p_,id_) for p_,id_ in zip(photopoints,ids)]

    def add_photopoint(self,photopoint,id_=None):
        """
        This method enables to register the given photpoint in the self.photopoints
        container (dict).
        
        Parameters
        ----------
        new_image: [string or astrobject's Image (or children)]

        - option -
        id_: [any]                 key used to access the photopoint from the _handler.
                                   id_ is set the photopoint's bandname if None
        
        Return
        ------
        Void
        """
        # --------------
        # - Define ID
        ID = id_ if id_ is not None else photopoint.bandname
        if self.has_data():
            if ID in self.list_id:
                i = 1
                while ID+"-%d"%i in self.list_id:
                    i+=1
                ID = ID+"-%d"%i
        # -------------------
        # - Record the point        
        self.photopoints[ID] = photopoint

    def writeto(self,filename,format="ascii",**kwargs):
        """
        Save the PhotoPointCollection following the astropy's Table 'write()' method.
        Such data will be accessible using the 'load()' method of the class.
        """
        self.data.write(filename,format=format,**kwargs)
        
    def load(self,filename,format="ascii",**kwargs):
        """
        """
        from .photometry import photopoint
        data = Table.read(filename,format=format)
        ids,pps = [],[]
        # - This way to be able to call create that might be more
        # generic than add_photopoints
        for pp in data:
            d = {}
            for i,k in enumerate(data.keys()):
                d[k] = pp[i]
            ids.append(d.pop("id"))
            pps.append(photopoint(**d))
            
        self.create(pps,ids,**kwargs)
        if "comments" in data.meta.keys():
            self._read_table_comment_(data.meta["comments"])

    def _read_table_comment_(self, comment):
        """ """
        warnings.warn("The following comments on the table are not saved:"+"\n".join(comment))
        pass
        
    # ------------------- #
    # - Getter          - #
    # ------------------- #
    def get(self,param,safeexit=True):
        """Loop over the photopoints (following the list_id sorting) to get the parameters
        using the photopoint.get() method.

        If safeexit is True NaN will be set to cases where the get(key) does not exist.
        Otherwise this raises a ValueError.
        
        Returns
        -------
        list
        """
        return [self.photopoints[id_].get(param,safeexit=safeexit)
                for id_ in self.list_id]

    # ------------------- #
    # - Setter          - #
    # ------------------- #
    def set_meta(self,key,values):
        """
        Assign to all photopoints of the instance a 'value' registered as 'key' in their meta dict.
        If the 'values' could either be a constant or an N-array where N is the number of photopoints

        Returns:
        --------
        Void
        """
        if "__iter__" not in values:
            values = [values]*self.nsources
        elif len(values)==1:
            values = [values[0]]*self.nsources
        elif len(values) !=self.nsources:
            raise ValueError("the given 'values', must provide a value for each photopoints (%d) or a unique value  %d given"%(self.nsources,len(values)))
        for id_,v in zip(self.list_id,values):
            self.photopoints[id_].meta[key] = v
    # ------------------- #
    # - Plot Stuff      - #
    # ------------------- #
    def show(self,mode="sed",savefile=None,toshow="flux",ax=None,
             cmap="jet",show=True,**kwargs):
        """
        """
        if mode.lower()=="sed":
            kwargs["function_of_time"] = False
            return self._show_(savefile=savefile,toshow=toshow,ax=ax,
                        cmap=cmap,show=show,**kwargs)
        if mode.lower()=="lightcurve":
            kwargs["function_of_time"] = True
            return self._show_(savefile=savefile,toshow=toshow,ax=ax,
                        cmap=cmap,show=show,**kwargs)
        

        
    # ========================== #
    # = Internal Stufff        = #
    # ========================== #
    def _show_(self,savefile=None,toshow="flux",ax=None,
                cmap="jet",show=True,**kwargs):
        """
        """
        import matplotlib.pyplot as mpl
        from ..utils.mpladdon import figout
        self._plot = {}
        # --------------------
        # --- INPUTS
        # - axes
        if ax is None:
            fig = mpl.figure(figsize=[8,8])
            ax  = fig.add_axes([0.1,0.1,0.8,0.8])
        elif "imshow" not in dir(ax):
            raise TypeError("The given 'ax' most likely is not a matplotlib axes. "+\
                             "No imshow available")
        else:
            fig = ax.figure
            
        # - Colors
        if type(cmap) is str:
            cmap = eval("mpl.cm.%s"%cmap)
        colors = kwargs.pop("color",[cmap((i-np.min(self.lbdas))/(np.max(self.lbdas)-np.min(self.lbdas))) for i in self.lbdas])
        prop = kwargs_update({"ms":10},**kwargs)
        # -------------
        # - Da Plot
        pl = [self.photopoints[id_].display(ax,toshow=toshow,color=c_,**prop)["plot"]
              for id_,c_ in zip(self.list_id,colors)]
        # -------------
        # - Out
        self._plot['ax'] = ax
        self._plot['fig'] = fig
        self._plot['plot'] = pl
        self._plot['prop'] = kwargs
        fig.figout(savefile=savefile,show=show)

    
    # ========================== #
    # = Properties             = #
    # ========================== #    
    @property
    def photopoints(self):
        """
        """
        return self._handler
    
    # ------------------ #
    # - On flight prop - #
    # ------------------ #
    # -- Bands
    @property
    def bandnames(self):
        """This returns an array of the recorded images' bandname (self.bandnames<==>self.get('bandname'))"""
        # -- This might be included in the add/remove image tools
        return self.get("bandname")

    @property
    def nbands(self):
        """The amount of diffenrent recorded bands"""
        return np.unique(self.bandnames)

    # -- Flux Variances etc.
    @property
    def lbdas(self):
        """The wavelength of every photopoints (self.lbdas<==>self.get(lbda'))"""
        return self.get("lbda")

    @property
    def fluxes(self):
        """The fluxes of every photopoints (self.fluxs<==>self.get('flux'))"""
        return self.get("flux")
    
    @property
    def fluxvars(self):
        """The flux variances of every photopoints (self.fluxvars<==>self.get('var'))"""
        return self.get("var")
    
    @property
    def mags(self):
        """The (AB) mag of every photopoints (self.mags<==>self.get('mag'))"""
        return self.get("mag")

    @property
    def magvars(self):
        """The (AB) mag variances of every photopoints (self.magvars<==>self.get('magvar'))"""
        return self.get("magvar")
    
    # -- Times
    @property
    def mjds(self):
        """The modified Julian Dates of every photopoints (self.mdjs<==>self.get('mjd'))"""
        return self.get("mjd")

    @property
    def metakeys(self):
        """ This is the list of all the meta keys known by at least one photopoints
        You can access these get from self.get(key)
        """
        return np.unique(np.concatenate(self.get("meta.keys()"))).tolist()
    
    # --------------
    # - Derived
    @property
    def data(self):
        """ The builds an astropy table containing the fundatemental parameters of the collection """
        # - Main
        maindata = [self.list_id,self.fluxes,self.fluxvars,self.lbdas,self.mjds,self.bandnames,
                    self.get("zp"),self.get("zpsys")]
        mainnames= ["id","flux","var","wavelength","mjd","bandname","zp","zpsystem"]
        # - Meta
        metaname = self.metakeys
        metadata = [self.get(metak) for metak in metaname]
        return Table(data=maindata+metadata,
                     names=mainnames+metaname)

########################################
#                                      #
# Hi Level Classes:  PhotoMap          #
#                                      #
########################################

class PhotoMap( PhotoPointCollection ):
    """
    """
    #__nature__ = "PhotoMap"
    
    def __init__(self, photopoints=None,coords=None,
                 filein=None,empty=False,wcs=None,**kwargs):
        """
        """
        self.__build__()
        if empty:
            return
        if filein is not None:
            self.load(filein,**kwargs)
            
        if photopoints is not None:
            self.create(photopoints,coords,wcs=wcs,**kwargs)
        
            
    def __build__(self):
        """
        """
        self._properties_keys = self._properties_keys+["wcsid"]
        self._side_properties_keys = self._side_properties_keys + \
          ["refmap","wcs"]
        super(PhotoMap,self).__build__()

    def _read_table_comment_(self, comments):
        """
        """
        for c in comments:
            key,value = c.split()
            if key == "wcsid":
                self._properties["wcsid"]=bool(value)
            else:
                print "comment not saved: ", c
                
    # =============================== #
    # = Building Methods            = #
    # =============================== #

    # ---------------- #
    # - SUPER THEM   - #
    # ---------------- #
    def create(self,photopoints,coords, wcs_coords=None,
               wcs=None,refmaps=None,**kwargs):
        """
        wcs_coords means that the coordinate are given in ra,dec.
        
        """
        super(PhotoMap,self).create(photopoints,ids=coords,**kwargs)
        if wcs is not None:
            self.set_wcs(wcs)
        if refmaps is not None:
            self.set_refmaps(wcs)
        
    def add_photopoint(self,photopoint,coords):
        """
        """
        if coords is None:
            raise ValueError("The coordinates of the photopoint are necessary")
        
        if type(coords) is str or type(coords) is np.string_:
            # -- If this failse, the coordinate format is not correct
            coords = self.id_to_coords(coords)
        elif np.shape(coords) != (2,):
            raise TypeError("the given coordinate must be a 2d array (x,y)/(ra,dec)")
        
        super(PhotoMap,self).add_photopoint(photopoint,self.coords_to_id(*coords))

    def writeto(self,filename,format="ascii.commented_header",**kwargs):
        comments = "".join(["# %s %s \n "%(key, value) for key,value in [["wcsid",self._wcsid]]])
        super(PhotoMap,self).writeto(filename,format,comment=comments,**kwargs)
        
    # =============================== #
    # = Main Methods                = #
    # =============================== #
    def coords_to_id(self,x,y):
        """ this enables to have consistent coordinate/id mapping """
        return "%.8f,%.8f"%(x,y)
    
    def id_to_coords(self,id):
        return np.asarray(id.split(","),dtype="float")

    # ------------- #
    # - SETTER    - #
    # ------------- #
    def set_wcs(self,wcs,force_it=False):
        """
        """
        if self.has_wcs() and force_it is False:
            raise AttributeError("'wcs' is already defined."+\
                    " Set force_it to True if you really known what you are doing")
                    
        from .astrometry import get_wcs
        self._side_properties["wcs"] = get_wcs(wcs,verbose=True)

    def set_refmap(self, photomap,force_it=False):
        """
        Set here the reference map associated to the current one.
        The ordering of the point must be consistant with that of the current
        photomap. 
        """
        if self.has_refmap() and force_it is False:
            raise AttributeError("'refmap' is already defined."+\
                    " Set force_it to True if you really known what you are doing")

        #if "__nature__" not in dir(photomap) or photomap.__nature__ != "PhotoMap":
        #    raise TypeError("The given reference map must be a astrobject PhotoMap")

        self._side_properties["refmap"] = photomap

    # ------------- #
    # - GETTER    - #
    # ------------- #
    def get_ids_around(self, ra, dec, radius):
        """
        Parameters:
        ----------
        ra, dec : [float]          Position in the sky *in degree*

        radius: [astropy.Quantity] distance of search, using astropy.units

        Return
        ------
        (SkyCoords.search_around_sky output)
        """
        from astropy import coordinates
        sky = coordinates.SkyCoord(ra=ra*units.degree, dec=dec*units.degree)
        ra_,dec_ = self.coords.T
        return coordinates.SkyCoord(ra=ra_*units.degree,dec=dec_*units.degree).search_around_sky(sky, radius)

    # ------------- #
    # - PLOTTER   - #
    # ------------- #
    def display_voronoy(self,ax=None,toshow="flux",wcs_coords=False,**kwargs):
        """
        """
        if ax is None:
            fig = mpl.figure(figsize=[8,8])
            ax  = fig.add_axes([0.1,0.1,0.8,0.8])
            ax.set_xlabel("x" if not wcs_coords else "Ra",fontsize = "x-large")
            ax.set_ylabel("y" if not wcs_coords else "Dec",fontsize = "x-large")
        elif "imshow" not in dir(ax):
            raise TypeError("The given 'ax' most likely is not a matplotlib axes. "+\
                             "No imshow available")
        else:
            fig = ax.figure

        from ..utils.mpladdon import voronoi_patchs
        # -----------------
        # - The plot itself
        out = ax.voronoi_patchs(self.radec if wcs_coords else self.xy,
                                self.get(toshow),**kwargs)
        ax.figure.canvas.draw()
        return out
        
    # =============================== #
    # = properties                  = #
    # =============================== #
    @property
    def radec(self):
        """ """
        if self._wcsid:
            return self._coords
        if not self.has_wcs():
            raise AttributeError("You need a wcs solution to convert radec to pixels. None set.")
        return self.wcs.pix2world(*self._coords.T)
    
    @property
    def xy(self):
        """ """
        if not self._wcsid:
            return self._coords
        if not self.has_wcs():
            raise AttributeError("You need a wcs solution to convert pixels to radec. None set.")
        return self.wcs.world2pix(*self._coords.T)
    
    @property
    def _coords(self):
        """ """
        return np.asarray([self.id_to_coords(id_) for id_ in self.list_id])
    @property
    def _wcsid(self):
        if self._properties["wcsid"] is None:
            warnings.warn("No information about the nature of the coordinate ids (wcs/pixel?). **WCS system assumed**")
            self._properties["wcsid"] = True
        return self._properties["wcsid"]
    
    # -------------
    # - WCS
    @property
    def wcs(self):
        return self._side_properties['wcs']
    
    def has_wcs(self):
        return self.wcs is not None
    # -------------
    # - RefMap
    @property
    def refmap(self):
        return self._side_properties['refmap']
    
    def has_refmap(self):
        return self.refmap is not None

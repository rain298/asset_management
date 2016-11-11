{
# The human-readable name of your module, displayed in the interface
        'name' : "Asset_management" ,
# A more extensive description
        'description' : """
        """,
# Which modules must be installed for this one to work
        'depends' : ['base'],
        'category': 'assetmanagement',
# data files which are always installed
        'data': [
                'security/ir.model.access.csv',
                'views/asset_management_view.xml',
                'views/asset_management_lend_view.xml',
                # 'views/asset_storage_workflow.xml',
                # 'views/asset_get_workflow.xml',
                #'views/asset_lend_workflow.xml',
               # 'views/asset_apply_workflow.xml',
                'templates.xml',
                'data.xml',
                'security/resource_security.xml',
                'views/asset_management_link.xml',
                'views/asset_management_menu.xml',

        ],
# data files which are only installed in "demonstration mode"
        'demo': ['demo.xml' ,
        ],
        'application': True,
        'qweb':[
                'static/src/xml/asset_management.xml',
            ],
}

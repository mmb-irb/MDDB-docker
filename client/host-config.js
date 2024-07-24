// Import default query fields
import defaultQueryFields from "src/utils/constants/query-fields";

// Set the default description
const DEFAULT_DESCRIPTION = <>
    <strong>MDposit</strong> is an open platform designed to provide web
    access to atomistic molecular dynamics (MD) simulations. The aim of
    this initiative is to ease and promote data sharing along the
    wide-world scientific community in order to contribute in research.
</>;

// Set default values for every host config fields
// These values are used to fill missing values
const DEFAUL_HOST_CONFIGURATION = {
    api: 'http://localhost:8081/rest/', // be aware that the port is the same of the docker-compose.yml file
    production: false,
    name: 'MDposit',
    favicon: 'mdposit_favicon',
    description: DEFAULT_DESCRIPTION,
    logo: 'logo-mdposit',
    primaryColor: '#808080', // Grey
    secondaryColor: '#fafafa', // Light grey
    searchExample: 'e.g. Orozco lab',
    optionsField: undefined, // No browser selector and no data summary pie chart by default
    optionsLabel: 'Options',
    optionsNiceNames: {},
    queryFields: defaultQueryFields,
};

// Set every host configuration
const HOST_CONFIGURATIONS = {
    // Testing
    'localhost': {
        api: 'http://localhost:8081/rest/', // be aware that the port is the same of the docker-compose.yml file
        primaryColor: '#707070', // Grey
    }
};

// Set the current host configuration
const HOST_CONFIG = HOST_CONFIGURATIONS['localhost'];

// Fill the host configuration gaps with default values
Object.entries(DEFAUL_HOST_CONFIGURATION).forEach(([ field, defaultValue ]) => {
    if (!HOST_CONFIG[field]) HOST_CONFIG[field] = defaultValue;
});

export default HOST_CONFIG;
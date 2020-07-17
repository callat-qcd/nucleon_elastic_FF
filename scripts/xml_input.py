import c51_mdwf_hisq as c51

def make_coherent_ff_xml(xmlini, params_in, prop_name, prop_file, dt, flav_spin):
    params = {k:v for k,v in params_in.items()}
    fin = open(xmlini, 'w')
    fin.write(head)
    ''' read all props '''
    params['OBJ_ID']    = prop_name
    params['OBJ_TYPE']  = 'LatticePropagator'
    if '.h5' not in prop_file:
        params['LIME_FILE'] = prop_file
        fin.write(qio_read % params)
    else:
        params['H5_FILE'] = prop_file
        if ens == 'a12m130':
            if params['si'] in [0, 8]:
                params['H5_PATH'] = '48_64'
                params['H5_OBJ_NAME'] = 'prop1'
            else:
                params['H5_PATH'] = ''
                params['H5_OBJ_NAME'] = 'prop'
        else:
            params['H5_PATH'] = ''
            params['H5_OBJ_NAME'] = 'prop'
        fin.write(hdf5_read % params)
    ''' read all seq props and do contractions '''
    for particle in params['particles']:
        params['PARTICLE'] = particle
        if '_np' in particle:
            t_sep = '-'+dt
        else:
            t_sep = dt
        params['T_SEP'] = t_sep
        for fs in flav_spin:
            flav,snk_spin,src_spin= fs.split('_')
            params['FLAV']        = flav
            params['SOURCE_SPIN'] = snk_spin
            params['SINK_SPIN']   = src_spin
            spin                  = snk_spin+'_'+src_spin
            params['FLAV_SPIN']   = fs
            seqprop_name          = c51.names['seqprop'] %params
            seqprop_file          = params['seqprop']+'/'+seqprop_name+'.'+params['SP_EXTENSION']
            params['LIME_FILE']   = seqprop_file
            params['OBJ_ID']      = seqprop_name
            params['SEQPROP_'+fs] = seqprop_name
            fin.write(qio_read % params)

        params['PROP_NAME'] = prop_name
        ''' make 3pt contractions '''
        params['CURR_4D'] = ''
        for ci,curr in enumerate(params['curr_4d']):
            params['CURR_4D'] += '        <elem>'+curr+'</elem>'
            if ci < len(params['curr_4d']) -1:
                params['CURR_4D'] += '\n'
        params['CURR_0P'] = ''
        for ci,curr in enumerate(params['curr_0p']):
            params['CURR_0P'] += '        <elem>'+curr+'</elem>'
            if ci < len(params['curr_0p']) -1:
                params['CURR_0P'] += '\n'
        fin.write(lalibe_formfac % params)
        ''' erase seqprops to reduce memory footprint '''
        for fs in flav_spin:
            fin.write(qio_erase %{'OBJ_ID':params['SEQPROP_'+fs]})

    fin.write(tail % params)
    fin.close()










head='''<?xml version="1.0"?>
<lalibe>
<Param>
  <InlineMeasurements>

'''

tail='''
  </InlineMeasurements>
   <nrow>%(NL)s %(NL)s %(NL)s %(NT)s</nrow>
</Param>

<Cfg>
 <cfg_type>SCIDAC</cfg_type>
 <cfg_file>%(CFG_FILE)s</cfg_file>
  <parallel_io>true</parallel_io>
</Cfg>
</lalibe>
'''

wflow_cfg = """<elem>
<Name>WILSON_FLOW</Name>
<Frequency>1</Frequency>
<Param>
  <version>1</version>
  <nstep>%(FLOW_STEP)s</nstep>
  <wtime>%(FLOW_TIME)s</wtime>
  <t_dir>-1</t_dir>
</Param>
<NamedObject>
  <gauge_in>%(CFG_PREFLOW)s</gauge_in>
  <gauge_out>%(CFG_FLOW)s</gauge_out>
</NamedObject>
</elem>

"""

hdf5_read='''<elem>
<Name>HDF5_READ_NAMED_OBJECT</Name>
<Frequency>1</Frequency>
<NamedObject>
  <object_id>%(OBJ_ID)s</object_id>
  <object_type>%(OBJ_TYPE)s</object_type>
</NamedObject>
<File>
  <file_name>%(H5_FILE)s</file_name>
  <path>/%(H5_PATH)s</path>
  <obj_name>%(H5_OBJ_NAME)s</obj_name>
</File>
</elem>

'''

hdf5_write='''<elem>
<Name>HDF5_WRITE_NAMED_OBJECT</Name>
<Frequency>1</Frequency>
<NamedObject>
  <object_id>%(OBJ_ID)s</object_id>
  <object_type>%(OBJ_TYPE)s</object_type>
</NamedObject>
<File>
  <file_name>%(H5_FILE)s</file_name>
  <path>/%(H5_PATH)s</path>
  <obj_name>%(H5_OBJ_NAME)s</obj_name>
</File>
</elem>

'''

qio_read='''<elem>
<Name>QIO_READ_NAMED_OBJECT</Name>
<Frequency>1</Frequency>
<NamedObject>
  <object_id>%(OBJ_ID)s</object_id>
  <object_type>%(OBJ_TYPE)s</object_type>
</NamedObject>
<File>
  <file_name>%(LIME_FILE)s</file_name>
  <file_volfmt>SINGLEFILE</file_volfmt>
  <parallel_io>true</parallel_io>
</File>
</elem>

'''

qio_erase='''<elem>
<Name>ERASE_NAMED_OBJECT</Name>
<Frequency>1</Frequency>
<NamedObject>
  <object_id>%(OBJ_ID)s</object_id>
</NamedObject>
</elem>

'''

qio_write='''<elem>
<Name>QIO_WRITE_NAMED_OBJECT</Name>
<Frequency>1</Frequency>
<NamedObject>
  <object_id>%(OBJ_ID)s</object_id>
  <object_type>%(OBJ_TYPE)s</object_type>
</NamedObject>
<File>
  <file_name>%(LIME_FILE)s</file_name>
  <file_volfmt>SINGLEFILE</file_volfmt>
  <parallel_io>true</parallel_io>
</File>
</elem>

'''

quda_nef='''<elem>
<Name>PROPAGATOR</Name>
<Frequency>1</Frequency>
<Param>
<version>10</version>
<quarkSpinType>%(QUARK_SPIN)s</quarkSpinType>
<obsvP>true</obsvP>
<numRetries>1</numRetries>
<FermionAction>
<FermAct>UNPRECONDITIONED_NEF</FermAct>
  <OverMass>%(M5)s</OverMass>
  <N5>%(L5)s</N5>
  <b5>%(B5)s</b5>
  <c5>%(C5)s</c5>
  <Mass>%(MQ)s</Mass>
  <FermionBC>
    <FermBC>SIMPLE_FERMBC</FermBC>
    <boundary>1 1 1 -1</boundary>
  </FermionBC>
</FermionAction>
<InvertParam>
<invType>QUDA_NEF_INVERTER</invType>
<DoCGNR>true</DoCGNR>
<MaxIter>%(MAX_ITER)s</MaxIter>
<RsdTarget>%(RSD_TARGET)s</RsdTarget>
<Delta>%(Q_DELTA)s</Delta>
<RsdToleranceFactor>%(RSD_TOL)s</RsdToleranceFactor>
<MaxResIncrease>1</MaxResIncrease>
<SolverType>CG</SolverType>
<Verbose>false</Verbose>
<AsymmetricLinop>false</AsymmetricLinop>
<CudaReconstruct>RECONS_12</CudaReconstruct>
<CudaSloppyPrecision>HALF</CudaSloppyPrecision>
<CudaSloppyReconstruct>RECONS_12</CudaSloppyReconstruct>
<AxialGaugeFix>false</AxialGaugeFix>
<AutotuneDslash>true</AutotuneDslash>
<MatPCType>EVEN_EVEN</MatPCType>
<checkSolution>false</checkSolution>
<NEFParams>
  <OverMass>%(M5)s</OverMass>
  <N5>%(L5)s</N5>
  <b5>%(B5)s</b5>
  <c5>%(C5)s</c5>
  <Mass>%(MQ)s</Mass>
  <clovCoeff>0</clovCoeff>
</NEFParams>
<AntiPeriodicT>true</AntiPeriodicT>
</InvertParam>
</Param>
<NamedObject>
  <gauge_id>default_gauge_field</gauge_id>
  <source_id>%(SRC_NAME)s</source_id>
  <prop_id>%(PROP_NAME)s</prop_id>
</NamedObject>
%(PROP_XML)s
</elem>

'''

shell_source='''<elem>
<Name>MAKE_SOURCE</Name>
<Frequency>1</Frequency>
<Param>
<version>6</version>
<Source>
    <version>1</version>
    <SourceType>SHELL_SOURCE</SourceType>
    <j_decay>3</j_decay>
    <t_srce>%(X0)s %(Y0)s %(Z0)s %(T0)s</t_srce>
    <SmearingParam>
        <wvf_kind>GAUGE_INV_GAUSSIAN</wvf_kind>
        <wvf_param>%(WF_S)s</wvf_param>
        <wvfIntPar>%(WF_N)s</wvfIntPar>
        <no_smear_dir>3</no_smear_dir>
    </SmearingParam>
</Source>
</Param>
<NamedObject>
  <gauge_id>default_gauge_field</gauge_id>
  <source_id>%(SRC_NAME)s</source_id>
</NamedObject>
</elem>

'''


shell_smearing='''
<elem>
<Name>SINK_SMEAR</Name>
<Frequency>1</Frequency>
<Param>
<version>5</version>
<Sink>
  <version>2</version>
  <SinkType>SHELL_SINK</SinkType>
  <j_decay>3</j_decay>
  <SmearingParam>
    <wvf_kind>GAUGE_INV_GAUSSIAN</wvf_kind>
    <wvf_param>%(WF_S)s</wvf_param>
    <wvfIntPar>%(WF_N)s</wvfIntPar>
    <no_smear_dir>3</no_smear_dir>
  </SmearingParam>
</Sink>
</Param>
<NamedObject>
  <gauge_id>default_gauge_field</gauge_id>
  <prop_id>%(PROP_NAME)s</prop_id>
  <smeared_prop_id>%(SMEARED_PROP)s</smeared_prop_id>
</NamedObject>
</elem>

'''

meson_spec='''<elem>
<Name>MESON_CONTRACTIONS</Name>
<MesonParams>
<p2_max>%(MESONS_PSQ_MAX)s</p2_max>
<particle_list>
    <elem>piplus</elem>
</particle_list>
<h5_file_name>%(SPEC_FILE)s</h5_file_name>
<obj_path>/%(H5_PATH)s</obj_path>
</MesonParams>
  <NamedObject>
   <up_quark>%(UP_QUARK)s</up_quark>
   <down_quark>%(DN_QUARK)s</down_quark>
  </NamedObject>
</elem>

'''
pi_k_spec='''<elem>
<Name>MESON_CONTRACTIONS</Name>
<MesonParams>
<p2_max>%(MESONS_PSQ_MAX)s</p2_max>
<particle_list>
    <elem>piplus</elem>
    <elem>kplus</elem>
    <elem>kminus</elem>
</particle_list>
<h5_file_name>%(HYPERSPEC_FILE)s</h5_file_name>
<obj_path>/%(H5_PATH)s</obj_path>
</MesonParams>
  <NamedObject>
   <up_quark>%(UP_QUARK)s</up_quark>
   <down_quark>%(DN_QUARK)s</down_quark>
   <strange_quark>%(STRANGE_QUARK)s</strange_quark>
  </NamedObject>
</elem>

'''

baryon_spec = '''  <elem>
<Name>BARYON_CONTRACTIONS</Name>
<Frequency>1</Frequency>
<BaryonParams>
    <ng_parity>true</ng_parity>
    <h5_file_name>%(SPEC_FILE)s</h5_file_name>
    <path>/%(H5_PATH)s</path>
%(BARYON_MOM)s
    <particle_list>
        <elem>proton</elem>
    </particle_list>
</BaryonParams>
<NamedObject>
    <up_quark>%(UP_QUARK)s</up_quark>
    <down_quark>%(DN_QUARK)s</down_quark>
</NamedObject>
</elem>

'''

hyperon_spec = '''  <elem>
<Name>BARYON_CONTRACTIONS</Name>
<Frequency>1</Frequency>
<BaryonParams>
    <ng_parity>true</ng_parity>
    <h5_file_name>%(HYPERSPEC_FILE)s</h5_file_name>
    <path>/%(H5_PATH)s</path>
%(BARYON_MOM)s
    <particle_list>
        <elem>octet</elem>
        <elem>decuplet</elem>
    </particle_list>
</BaryonParams>
<NamedObject>
    <up_quark>%(UP_QUARK)s</up_quark>
    <down_quark>%(DN_QUARK)s</down_quark>
    <strange_quark>%(STRANGE_QUARK)s</strange_quark>
</NamedObject>
</elem>

'''

pipi_spec = '''<elem>
  <Name>PIPI_SCATTERING</Name>
  <PipiParams>
    <p2_max>%(MM_REL_MOM)s</p2_max>
    <ptot2_max>%(MM_TOT_MOM)s</ptot2_max>
    <diagrams>0</diagrams>
    <h5_file_name>%(PIPI_SCAT_FILE)s</h5_file_name>
    <obj_path>/PS</obj_path>
  </PipiParams>
  <NamedObject>
    <light_prop>%(PROP_LIGHT)s</light_prop>
  </NamedObject>
</elem>

<elem>
  <Name>PIPI_SCATTERING</Name>
  <PipiParams>
    <p2_max>%(MM_REL_MOM)s</p2_max>
    <ptot2_max>%(MM_TOT_MOM)s</ptot2_max>
    <diagrams>0</diagrams>
    <h5_file_name>%(PIPI_SCAT_FILE)s</h5_file_name>
    <obj_path>/SS</obj_path>
  </PipiParams>
  <NamedObject>
    <light_prop>SS_%(PROP_LIGHT)s</light_prop>
  </NamedObject>
</elem>

'''

pik_spec = '''<elem>
  <Name>PIPI_SCATTERING</Name>
  <PipiParams>
    <p2_max>%(MM_REL_MOM)s</p2_max>
    <ptot2_max>%(MM_TOT_MOM)s</ptot2_max>
    <diagrams>0</diagrams>
    <h5_file_name>%(PIPI_SCAT_FILE)s</h5_file_name>
    <obj_path>/PS</obj_path>
  </PipiParams>
  <NamedObject>
    <light_prop>%(PROP_LIGHT)s</light_prop>
    <strange_prop>%(PROP_STRANGE)s</strange_prop>
  </NamedObject>
</elem>

<elem>
  <Name>PIPI_SCATTERING</Name>
  <PipiParams>
    <p2_max>%(MM_REL_MOM)s</p2_max>
    <ptot2_max>%(MM_TOT_MOM)s</ptot2_max>
    <diagrams>0</diagrams>
    <h5_file_name>%(PIPI_SCAT_FILE)s</h5_file_name>
    <obj_path>/SS</obj_path>
  </PipiParams>
  <NamedObject>
    <light_prop>SS_%(PROP_LIGHT)s</light_prop>
    <strange_prop>SS_%(PROP_STRANGE)s</strange_prop>
  </NamedObject>
</elem>

'''



lalibe_seqsource='''<elem>
    <Name>LALIBE_SEQSOURCE</Name>
    <Frequency>1</Frequency>
    <SeqSourceParams>
      <particle>%(PARTICLE)s</particle>
      <flavor>%(FLAV)s</flavor>
      <source_spin>%(SOURCE_SPIN)s</source_spin>
      <sink_spin>%(SINK_SPIN)s</sink_spin>
      <sink_mom>%(M0)s %(M1)s %(M2)s</sink_mom>
    </SeqSourceParams>
    <NamedObject>
        <gauge_id>default_gauge_field</gauge_id>
        <up_quark>%(UP_QUARK)s</up_quark>
        <down_quark>%(DOWN_QUARK)s</down_quark>
        <seqsource_id>%(SEQSOURCE)s</seqsource_id>
    </NamedObject>
</elem>

'''

coherent_seqsrc='''<elem>
    <Name>COHERENT_SEQSOURCE</Name>
    <Frequency>1</Frequency>
    <SinkParams>
        <t_sep>%(T_SEP)s</t_sep>
        <j_decay>3</j_decay>
    </SinkParams>
    <NamedObject>
        <sink_ids>
%(SEQSOURCE_LIST)s
        </sink_ids>
        <result_sink>%(COHERENT_SEQSOURCE)s</result_sink>
    </NamedObject>
</elem>

'''

add_8_coherent_sinks='''
<elem>
<Name>MULTI_PROP_ADD</Name>
<Frequency>1</Frequency>
<PropWeights>
<delete_props>false</delete_props>
<weights>1 1 1 1 1 1 1 1</weights>
</PropWeights>
<NamedObject>
<prop_ids>
    <elem>%(SEQSOURCE_0)s</elem>
    <elem>%(SEQSOURCE_1)s</elem>
    <elem>%(SEQSOURCE_2)s</elem>
    <elem>%(SEQSOURCE_3)s</elem>
    <elem>%(SEQSOURCE_4)s</elem>
    <elem>%(SEQSOURCE_5)s</elem>
    <elem>%(SEQSOURCE_6)s</elem>
    <elem>%(SEQSOURCE_7)s</elem>
</prop_ids>
<result_prop>%(COHERENT_SEQSOURCE)s</result_prop>
</NamedObject>
</elem>

'''

lalibe_formfac='''<elem>
<annotation>
  4D CORRELATORS
</annotation>
<Name>LALIBE_BAR3PTFN</Name>
<Frequency>1</Frequency>
<Param>
    <version>7</version>
    <j_decay>3</j_decay>
    <currents>
%(CURR_4D)s
    </currents>
    <h5_file_name>%(THREE_PT_FILE_4D)s</h5_file_name>
    <path>/</path>
</Param>
<NamedObject>
    <gauge_id>default_gauge_field</gauge_id>
    <prop_id>%(PROP_NAME)s</prop_id>
    <seqprops>
        <elem>
            <seqprop_id>%(SEQPROP_UU_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_UU_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
    </seqprops>
</NamedObject>
</elem>

<elem>
<annotation>
  0 MOMENTUM for all charges
</annotation>
<Name>LALIBE_BAR3PTFN</Name>
<Frequency>1</Frequency>
<Param>
    <version>7</version>
    <j_decay>3</j_decay>
    <currents>
%(CURR_0P)s
    </currents>
    <p2_max>0</p2_max>
    <h5_file_name>%(THREE_PT_FILE)s</h5_file_name>
    <path>/</path>
</Param>
<NamedObject>
    <gauge_id>default_gauge_field</gauge_id>
    <prop_id>%(PROP_NAME)s</prop_id>
    <seqprops>
        <elem>
            <seqprop_id>%(SEQPROP_UU_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_UU_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
    </seqprops>
</NamedObject>
</elem>

'''

lalibe_formfac_old='''<elem>
<annotation>
  SPECIFIED MOMENTUM
</annotation>
<Name>LALIBE_BAR3PTFN</Name>
<Frequency>1</Frequency>
<Param>
    <version>7</version>
    <j_decay>3</j_decay>
    <currents>
%(CURR_P)s
    </currents>
    <mom_list>
        <elem>0 0 0</elem>
        <elem>1 0 0</elem>
        <elem>-1 0 0</elem>
        <elem>0 1 0</elem>
        <elem>0 -1 0</elem>
        <elem>0 0 1</elem>
        <elem>0 0 -1</elem>
        <elem>2 0 0</elem>
        <elem>-2 0 0</elem>
        <elem>0 2 0</elem>
        <elem>0 -2 0</elem>
        <elem>0 0 2</elem>
        <elem>0 0 -2</elem>
        <elem>3 0 0</elem>
        <elem>-3 0 0</elem>
        <elem>0 3 0</elem>
        <elem>0 -3 0</elem>
        <elem>0 0 3</elem>
        <elem>0 0 -3</elem>
        <elem>4 0 0</elem>
        <elem>-4 0 0</elem>
        <elem>0 4 0</elem>
        <elem>0 -4 0</elem>
        <elem>0 0 4</elem>
        <elem>0 0 -4</elem>
    </mom_list>
    <h5_file_name>%(THREE_PT_FILE)s</h5_file_name>
    <path>/</path>
</Param>
<NamedObject>
    <gauge_id>default_gauge_field</gauge_id>
    <prop_id>%(PROP_NAME)s</prop_id>
    <seqprops>
        <elem>
            <seqprop_id>%(SEQPROP_UU_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_UU_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
    </seqprops>
</NamedObject>
</elem>

<elem>
<annotation>
  4D CORRELATORS
</annotation>
<Name>LALIBE_BAR3PTFN</Name>
<Frequency>1</Frequency>
<Param>
    <version>7</version>
    <j_decay>3</j_decay>
    <currents>
%(CURR_4D)s
    </currents>
    <h5_file_name>%(THREE_PT_FILE_4D)s</h5_file_name>
    <path>/</path>
</Param>
<NamedObject>
    <gauge_id>default_gauge_field</gauge_id>
    <prop_id>%(PROP_NAME)s</prop_id>
    <seqprops>
        <elem>
            <seqprop_id>%(SEQPROP_UU_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_UU_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
    </seqprops>
</NamedObject>
</elem>

<elem>
<annotation>
  0 MOMENTUM for a few correlators
</annotation>
<Name>LALIBE_BAR3PTFN</Name>
<Frequency>1</Frequency>
<Param>
    <version>7</version>
    <j_decay>3</j_decay>
    <currents>
%(CURR_0P)s
    </currents>
    <p2_max>0</p2_max>
    <h5_file_name>%(THREE_PT_FILE)s</h5_file_name>
    <path>/</path>
</Param>
<NamedObject>
    <gauge_id>default_gauge_field</gauge_id>
    <prop_id>%(PROP_NAME)s</prop_id>
    <seqprops>
        <elem>
            <seqprop_id>%(SEQPROP_UU_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_UU_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_up_up)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
        <elem>
            <seqprop_id>%(SEQPROP_DD_dn_dn)s</seqprop_id>
            <gamma_insertion>0</gamma_insertion>
        </elem>
    </seqprops>
</NamedObject>
</elem>

'''

dd_pairs = '''<elem>
  <Name>USQCD_WRITE_DD_PAIRS_PROP</Name>
  <Frequency>1</Frequency>
  <Param>
    <OutputFile>%(PROP_DIR)s/%(PROP_ID_DD)s</OutputFile>
    <OutputVolfmt>SINGLEFILE</OutputVolfmt>
    <Precision>single</Precision>
    <parallel_io>true</parallel_io>
  </Param>
  <NamedObject>
<prop_id>%(PROP_ID)s</prop_id>
<gauge_id>default_gauge_field</gauge_id>
  </NamedObject>
</elem>

'''

src_sh_stag = '''<elem>
<Name>MAKE_SOURCE_STAG</Name>
<Frequency>1</Frequency>
<Param>
<version>6</version>
<Source>
  <version>2</version>
  <SourceType>SHELL_SOURCE</SourceType>
  <j_decay>3</j_decay>
  <t_srce>%(X0)s %(Y0)s %(Z0)s %(T0)s</t_srce>
  <SmearingParam>
    <wvf_kind>GAUGE_INV_GAUSSIAN</wvf_kind>
    <wvf_param>%(WF_S)s</wvf_param>
    <wvfIntPar>%(WF_N)s</wvfIntPar>
    <no_smear_dir>3</no_smear_dir>
  </SmearingParam>
  <Displacement>
    <version>1</version>
    <DisplacementType>SCALAR_STAG_FLAV</DisplacementType>
    <mu>1</mu>
    <nu>2</nu>
  </Displacement>
</Source>
</Param>
<NamedObject>
  <gauge_id>%(GAUGE_FIELD)s</gauge_id>
  <source_id>%(SRC_ID)s</source_id>
</NamedObject>
</elem>

'''

src_pt_stag = '''<elem>
<Name>MAKE_SOURCE_STAG</Name>
<Frequency>1</Frequency>
<Param>
<version>6</version>
<Source>
  <version>2</version>
  <SourceType>POINT_SOURCE</SourceType>
  <j_decay>3</j_decay>
  <t_srce>%(X0)s %(Y0)s %(Z0)s %(T0)s</t_srce>
  <Displacement>
    <version>1</version>
    <DisplacementType>SCALAR_STAG_FLAV</DisplacementType>
    <mu>1</mu>
    <nu>2</nu>
  </Displacement>
</Source>
</Param>
<NamedObject>
  <gauge_id>%(GAUGE_FIELD)s</gauge_id>
  <source_id>%(SRC_ID)s</source_id>
</NamedObject>
</elem>

'''

stag_src_write = '''<elem>
 <Name>MILC_WRITE_STAGGERED_SOURCE</Name>
 <Frequency>1</Frequency>
 <Param>
   <OutputFile>%(FILE_DIR)s/%(FILE_NAME)s</OutputFile>
   <OutputVolfmt>SINGLEFILE</OutputVolfmt>
   <Precision>single</Precision>
   <parallel_io>true</parallel_io>
   <t_slice>%(T0)s</t_slice>
 </Param>
 <NamedObject>
   <source_id>%(SRC_ID)s</source_id>
 </NamedObject>
</elem>

'''


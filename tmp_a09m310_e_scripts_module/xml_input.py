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
<FermAct>NEF</FermAct>
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
<CudaReconstruct>RECONS_NONE</CudaReconstruct>
<CudaSloppyPrecision>HALF</CudaSloppyPrecision>
<CudaSloppyReconstruct>RECONS_12</CudaSloppyReconstruct>
<AxialGaugeFix>false</AxialGaugeFix>
<AutotuneDslash>true</AutotuneDslash>
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
            <elem>%(SEQSOURCE_0)s</elem>
            <elem>%(SEQSOURCE_1)s</elem>
            <elem>%(SEQSOURCE_2)s</elem>
            <elem>%(SEQSOURCE_3)s</elem>
            <elem>%(SEQSOURCE_4)s</elem>
            <elem>%(SEQSOURCE_5)s</elem>
            <elem>%(SEQSOURCE_6)s</elem>
            <elem>%(SEQSOURCE_7)s</elem>
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
  SPECIFIED MOMENTUM
</annotation>
<Name>LALIBE_BAR3PTFN</Name>
<Frequency>1</Frequency>
<Param>
    <version>7</version>
    <j_decay>3</j_decay>
    <currents>
%(CURR_P)s
<annotation>
        <elem>S</elem>
        <elem>P</elem>
        <elem>V1</elem>
        <elem>V2</elem>
        <elem>V3</elem>
        <elem>V4</elem>
        <elem>A1</elem>
        <elem>A2</elem>
        <elem>A3</elem>
        <elem>A4</elem>
</annotation>
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
<annotation>
        <elem>S</elem>
        <elem>P</elem>
        <elem>V1</elem>
        <elem>V2</elem>
        <elem>V3</elem>
        <elem>V4</elem>
        <elem>A1</elem>
        <elem>A2</elem>
        <elem>A3</elem>
        <elem>A4</elem>
</annotation>
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
<annotation>
      <elem>T12</elem>
      <elem>T34</elem>
      <elem>CHROMO_MAG</elem>
</annotation>
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
